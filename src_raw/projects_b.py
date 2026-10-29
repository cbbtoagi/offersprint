# -*- coding: utf-8 -*-
"""项目实战原始题库数据（第二批，proj-006 ~ proj-010，纯数据文件，顶部不 import）。"""

PROJECTS = [
    {
        "id": "proj-006",
        "name": "KV Cache + 连续批处理：推理引擎雏形",
        "domain": "transformer",
        "level": "进阶",
        "tags": ["推理优化", "vLLM 思想"],
        "summaryMd": r'''从零搭一个带 KV cache 的解码循环，实现 prefill/decode 分离、按 slot 的连续批处理调度器和 PagedAttention 分页显存管理，把 vLLM 的核心思想浓缩进 150 行以内。面试讲这个项目最加分的是：不背结论，当场手推 KV cache 显存公式、讲清 decode 阶段为什么是访存瓶颈，并把每段代码对应到 vLLM 论文的具体机制。''',
        "bodyMd": r'''## 背景与思路

自回归解码最朴素的实现是：每生成一个 token，把整条序列重算一遍 attention。这意味着第 t 步要重复计算前 t-1 个 token 的 K/V，总计算量 $O(L^2)$ 且随长度平方增长——而实际上第 t 步真正"新"的只有最后一个 token。KV cache 的思路就是缓存每层已算好的 K/V，新 token 只算自己的 K/V 并拼接历史，把 decode 一步的计算量降到 $O(L)$。

顺着这个优化自然引出推理引擎的三个核心问题，也就是本项目要实现的三个组件：

1. **prefill/decode 分离**：prefill 一次性并行处理整条 prompt（算力密集），decode 每次只处理 1 个 token（访存密集）。两阶段计算特征完全不同，必须分开调度。
2. **连续批处理（continuous batching）**：静态 batching 里一个 batch 的显存要等最长的那条请求结束才释放；连续批处理每步解码完一条就立刻腾出 slot 给新请求，显存从"木桶最短板"变成"实时回收"，vLLM 实测吞吐提升 2~4 倍。
3. **PagedAttention 分页**：KV cache 按固定大小 block 分配，逻辑序列通过页表映射到物理块。序列增长时按块追加而非按 max_len 整段预留，消除内部碎片，还免费获得前缀共享（copy-on-write）能力。

## 架构设计

组件关系：`KVCacheAttention`（缓存拼接 + 因果 mask）→ `TinyEngine`（把注意力包成 prefill/decode 两个入口）→ `ContinuousScheduler`（slot 池，每步同步 decode，完成的槽位立刻回收）→ `BlockManager`（页表 + 空闲块池 + 显存估算）。与真实 vLLM 的映射：KVCacheAttention 对应 kernel 层（PagedAttention kernel / FlashAttention），TinyEngine 对应模型执行器，ContinuousScheduler 对应 scheduler，BlockManager 对应 BlockSpaceManager。

## 关键组件实现

### KV cache 注意力与两阶段解码

先看注意力本身：cache 是上一次的 (K, V)，新 token 的 K/V 拼到序列维后面。注意因果 mask 只在 prefill（T>1）时需要，decode 时单 token 天然能看到全部历史，不需要 mask。

```python
import torch
import torch.nn.functional as F

class KVCacheAttention(torch.nn.Module):
    # 带 KV cache 的因果注意力：新 token 的 K/V 拼到历史 cache 后面。

    def __init__(self, d_model, n_heads):
        super().__init__()
        self.n_heads = n_heads
        self.head_dim = d_model // n_heads
        self.wq = torch.nn.Linear(d_model, d_model, bias=False)
        self.wk = torch.nn.Linear(d_model, d_model, bias=False)
        self.wv = torch.nn.Linear(d_model, d_model, bias=False)
        self.wo = torch.nn.Linear(d_model, d_model, bias=False)

    def forward(self, x, cache=None):
        # x: (B, T, D)；cache: 上一次的 (K, V)，各为 (B, H, L, Dh)，首步为 None
        B, T, D = x.shape
        H, Dh = self.n_heads, self.head_dim
        q = self.wq(x).view(B, T, H, Dh).transpose(1, 2)     # (B, H, T, Dh)
        k_new = self.wk(x).view(B, T, H, Dh).transpose(1, 2)
        v_new = self.wv(x).view(B, T, H, Dh).transpose(1, 2)
        if cache is None:
            k, v = k_new, v_new                              # prefill：无历史
        else:
            k = torch.cat([cache[0], k_new], dim=2)          # decode：拼接历史 K/V
            v = torch.cat([cache[1], v_new], dim=2)
        L = k.size(2)
        scores = q @ k.transpose(2, 3) / (Dh ** 0.5)         # (B, H, T, L)
        if T > 1:
            # prefill 才需要因果 mask：第 i 个 query 是全局第 (L-T+i) 个位置
            mask = torch.triu(torch.ones(T, L, dtype=torch.bool, device=x.device),
                              diagonal=L - T + 1)
            scores = scores.masked_fill(mask, float("-inf"))
        attn = F.softmax(scores, dim=-1)
        out = (attn @ v).transpose(1, 2).reshape(B, T, D)
        return self.wo(out), (k, v)                          # 返回新 cache 供下一步用
```

两阶段解码循环：prefill 整条 prompt 只跑一次，之后每步只喂一个新 token。

```python
def decode_greedy(model, emb, vocab_head, prompt_ids, eos_id, max_new):
    cache = None
    x = emb(torch.tensor([prompt_ids]))                      # (1, P, D)
    h, cache = model(x, cache)                               # prefill：并行算整条 prompt
    logits = vocab_head(h[:, -1])                            # 只需最后一个位置的 logits
    out_ids = []
    for _ in range(max_new):
        tok = int(logits.argmax(dim=-1))                     # 贪心采样
        out_ids.append(tok)
        if tok == eos_id:
            break
        x = emb(torch.tensor([[tok]]))                       # decode：每次只算 1 个 token
        h, cache = model(x, cache)
        logits = vocab_head(h[:, -1])
    return out_ids
```

### 连续批处理调度器

slot 模型：每个槽位是一条进行中的序列，持有自己的 token 列表和 KV cache。调度器每步把所有活跃 slot 同步 decode 一步，谁先结束谁先释放——这就是与静态 batching 的本质区别。

```python
class TinyEngine:
    # 把注意力模块包成 prefill / decode_step 两个入口（真实引擎是完整 LLM，这里单层示意）。

    def __init__(self, model, emb, vocab_head, eos_id):
        self.model, self.emb, self.head, self.eos_id = model, emb, vocab_head, eos_id

    def prefill(self, token_ids):
        x = self.emb(torch.tensor([token_ids]))
        h, cache = self.model(x)                             # T>1 自动加因果 mask
        return h, cache

    def decode_step(self, last_ids, caches):
        outs, new_caches = [], []
        for tid, cache in zip(last_ids, caches):
            h, cache = self.model(self.emb(torch.tensor([[tid]])), cache)
            outs.append(int(self.head(h[:, -1]).argmax(dim=-1)))
            new_caches.append(cache)
        return outs, new_caches


class SequenceSlot:
    # 一个槽位对应一条进行中的请求（类比 vLLM 的 Sequence）。

    def __init__(self, seq_id, prompt, max_new):
        self.seq_id = seq_id
        self.token_ids = list(prompt)    # 含 prompt 的完整 token 序列
        self.cache = None                # 该序列独立的 KV cache
        self.generated = 0
        self.max_new = max_new
        self.done = False


class ContinuousScheduler:
    # 最简连续批处理：每步活跃序列同步 decode，完成的槽位立刻回收给新请求。

    def __init__(self, engine, max_slots):
        self.engine = engine
        self.max_slots = max_slots
        self.waiting = []                # 排队中的请求
        self.running = [None] * max_slots

    def add_request(self, seq_id, prompt, max_new):
        self.waiting.append(SequenceSlot(seq_id, prompt, max_new))
        self.fill_free_slots()

    def fill_free_slots(self):
        for i, slot in enumerate(self.running):
            if slot is None and self.waiting:
                seq = self.waiting.pop(0)
                # 入槽先 prefill；真实系统用 chunked prefill 把长 prompt 切块，
                # 防止一条超长 prompt 霸占算力、饿死其他 decode 请求
                _, cache = self.engine.prefill(seq.token_ids)
                seq.cache = cache
                self.running[i] = seq

    def step(self):
        active = [(i, s) for i, s in enumerate(self.running) if s is not None]
        if not active:
            return []
        last_ids = [s.token_ids[-1] for _, s in active]
        toks, caches = self.engine.decode_step(last_ids, [s.cache for _, s in active])
        finished = []
        for (i, s), tok, cache in zip(active, toks, caches):
            s.token_ids.append(tok)
            s.cache = cache
            s.generated += 1
            if tok == self.engine.eos_id or s.generated >= s.max_new:
                s.done = True
                finished.append((i, s))
        for i, _ in finished:
            self.running[i] = None       # 不等整批结束，立刻释放槽位
        self.fill_free_slots()           # 排队请求即刻补入
        return finished
```

### PagedAttention 分页与显存估算

KV cache 最大的浪费来自"按 max_len 预分配"：一条实际只生成 100 token 的请求，按 8192 预留就浪费了 98%。分页思想来自操作系统：KV 按 block 切，页表记录逻辑序列→物理块的映射，块内连续、块间可以任意离散。

```python
class BlockManager:
    # PagedAttention 分页：KV cache 按 block 分配，逻辑序列经页表映射到物理块。

    def __init__(self, num_blocks, block_size):
        self.block_size = block_size
        self.free_blocks = list(range(num_blocks))   # 物理块空闲池
        self.page_table = {}                          # seq_id -> [物理块 id]
        self.seq_lens = {}                            # seq_id -> 当前 token 数

    def allocate(self, seq_id, num_tokens):
        n_blocks = -(-num_tokens // self.block_size)  # 向上取整，按需分配不预留 max_len
        if len(self.free_blocks) < n_blocks:
            raise RuntimeError("显存不足，触发抢占或排队")
        self.page_table[seq_id] = [self.free_blocks.pop() for _ in range(n_blocks)]
        self.seq_lens[seq_id] = num_tokens

    def append(self, seq_id, num_new=1):
        # 只在跨越块边界时追加一个块；块内增长零拷贝
        if self.seq_lens[seq_id] + num_new > len(self.page_table[seq_id]) * self.block_size:
            if not self.free_blocks:
                raise RuntimeError("显存不足")
            self.page_table[seq_id].append(self.free_blocks.pop())
        self.seq_lens[seq_id] += num_new

    def free(self, seq_id):
        self.free_blocks.extend(self.page_table.pop(seq_id))  # O(1) 归还整条序列


def kv_cache_gb(n_layers, n_kv_heads, head_dim, total_tokens, bytes_per_elem=2):
    # 显存公式：2(K 和 V 各一份) * 层数 * KV 头数 * head_dim * 总 token 数 * 字节数。
    per_token = 2 * n_layers * n_kv_heads * head_dim * bytes_per_elem
    return per_token * total_tokens / 1024 ** 3
```

## 深挖追问

**Q1：Llama-3-8B 在 8K 上下文、256 并发下 KV cache 要多少显存？**
按公式代入：$M = 2 \times 32 \times 8 \times 128 \times L \times 2$ 字节 = 128KB/token（32 层、GQA 8 个 KV 头、head_dim 128、bf16）。$8K \times 256 = 200$ 万 token，共 256GB。所以生产环境 KV cache 通常比权重本身（8B × 2B = 16GB）大一个数量级，GQA 和 8bit/4bit KV 量化才成为标配。

**Q2：为什么 prefill 算力密集、decode 访存密集？**
prefill 每个 token 要和所有 token 算 attention，FLOPs 随序列长度增长，GPU 算力被吃满；decode 每步只有 1 个 token，FLOPs 极少，但每生成一个 token 要把全部权重和全部 KV 从显存读一遍，带宽成为瓶颈。推论：decode 阶段增大 batch 几乎不增延迟（带宽没饱和前），投机解码本质也是把访存密集任务变成算力密集任务来提速。

**Q3：PagedAttention 相对"整段连续预留"省在哪？**
三个来源：按需增长不预留 max_len；块粒度分配几乎无内部碎片（浪费 < 1 个 block）；任意空闲块都能用，显存碎片化不影响分配。顺带收益是前缀共享：多条请求共享同一 system prompt 的物理块，copy-on-write 只在发生修改时复制。

**Q4：连续批处理的调度粒度与公平性？**
vLLM 是 token 级别的调度：每一步重新选择本步要跑的序列集合，而不是锁死一个 batch。超长 prompt 用 chunked prefill 切成小块插进 decode 流，防止饿死其他请求；显存不足时按优先级抢占（swap 到 CPU 或直接丢弃重算）。

**Q5：prefill 和 decode 分离后还能做什么？**
两阶段可以各自优化：prefill 用序列并行、decode 用专用 kernel（PagedAttention/FlashDecoding）；还能做 prefix caching（共享前缀只 prefill 一次）、speculative decoding（draft 模型一次生成多个候选再并行验证）。能答出这些，说明理解的是推理系统而不是单个 trick。

## 面试加分点

- 能当场手推显存公式并给出数量级（8B 模型 8K 上下文 KV 是权重的十几倍），而不是背结论；
- 讲 decode 的访存密集时引到"加 batch 不增延迟""投机解码"，展示系统视角；
- 把三段代码分别对应到 vLLM 论文的 PagedAttention kernel、scheduler、BlockSpaceManager，证明读过源码；
- 主动提 chunked prefill、prefix caching、KV 量化作为延伸，比只答"连续批处理省显存"高一档。''',
    },
    {
        "id": "proj-007",
        "name": "ReAct Agent Harness 最小实现",
        "domain": "agent",
        "level": "经典",
        "tags": ["Agent", "工具调用"],
        "summaryMd": r'''单文件实现一个 ReAct Agent Harness：用装饰器把 Python 函数注册成带 JSON schema 的工具，跑通"思考→调工具→观察→再思考"的循环，支持错误回灌、上下文压缩和子 agent。面试讲这个项目最加分的是：能逐点说出它与 Claude Code / Codex CLI 的设计映射——system prompt 分层、工具注册表、循环控制、compaction、subagent——证明理解的是产品级 agent 系统而不是玩具 demo。''',
        "bodyMd": r'''## 背景与思路

Agent 的本质是：LLM + 工具 + 循环。LLM 单次推理没有外部信息、没有副作用，把它放进一个循环里，每步让它决定"调哪个工具、带什么参数"，把工具结果喂回上下文再推理，就得到了能完成开放任务的 agent。这个框架最早由 ReAct（Yao et al., 2022）命名：Reasoning（思考下一步做什么）与 Acting（执行工具）交替进行，观察结果后再思考。

工程上的关键决定是：工具调用不靠 prompt 里"请你输出 JSON"这种软约束，而是用 function calling 协议——每个工具描述成 JSON schema 传给模型，模型输出结构化的 tool_call。这样的输出可校验、可重试、参数类型明确，是所有生产级 agent（Claude Code、Codex CLI）共同的地基。

## 架构设计

单文件四件套：`Tool`（装饰器注册函数，用 inspect 读签名和类型标注自动生成 JSON schema，对齐 OpenAI function calling 格式）；`AgentLoop`（ReAct 主循环，max_steps 上限，工具异常以 tool 角色消息回灌让模型自纠错）；`compact()`（上下文超阈值时把旧消息交给模型摘要，只保留最近几轮原文）；`SubAgent`（子任务拿独立上下文和独立步数上限，主 agent 只看到最终结论）。

## 关键组件实现

### 工具注册表与 JSON schema

```python
import inspect
import json

TYPE_MAP = {float: "number", int: "integer", str: "string", bool: "boolean"}

class Tool:
    # 把普通 Python 函数包装成带 JSON schema 的工具。

    def __init__(self, func):
        self.func = func
        self.name = func.__name__
        self.doc = (func.__doc__ or "").strip()
        hints = inspect.getfullargspec(func).annotations
        self.params = {k: v for k, v in hints.items() if k != "return"}

    def to_schema(self):
        # 从函数签名自动生成 function calling 格式的 schema
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.doc,
                "parameters": {
                    "type": "object",
                    "properties": {
                        k: {"type": TYPE_MAP.get(v, "string")} for k, v in self.params.items()
                    },
                    "required": list(self.params.keys()),
                },
            },
        }


TOOLS = {}

def register_tool(func):
    # 装饰器注册；真实 harness 里工具的 name/description 会写进 system prompt 固定段落
    TOOLS[func.__name__] = Tool(func)
    return func


@register_tool
def add(a: float, b: float) -> float:
    '计算两个数字之和。'    # 单引号 docstring：Tool 从 __doc__ 读取它生成 schema
    return a + b


@register_tool
def search_web(query: str) -> str:
    '搜索网页并返回结果摘要。'
    return "search results for: " + query   # 真实实现换成搜索 API 调用
```

### ReAct 循环与错误回灌

```python
SYSTEM_PROMPT = (
    "你是 AI 助手。遇到需要计算或查询的问题时调用工具，"
    "获得结果后继续思考，直到能给出最终答案。"
    "需要调工具时输出 tool_call JSON，否则输出 final_answer JSON。"
)

class AgentLoop:
    # ReAct 主循环：思考 -> 调工具 -> 观察 -> 再思考，直到 final answer 或超步数。

    def __init__(self, llm, tools, max_steps=8):
        self.llm = llm            # 提供 chat(messages, tools) 的客户端
        self.tools = tools
        self.max_steps = max_steps

    def run(self, task):
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": task},
        ]
        schemas = [t.to_schema() for t in self.tools.values()]
        for _ in range(self.max_steps):
            resp = self.llm.chat(messages, tools=schemas)
            if resp.get("type") == "final_answer":
                messages.append({"role": "assistant", "content": resp["text"]})
                return resp["text"]
            call = resp["tool_call"]                     # {"name": ..., "arguments": {...}}
            result = self.execute(call, messages)
            if result["error"] is not None:
                # 错误回灌：不中断流程，模型看到报错后自己修正参数重试
                messages.append({"role": "tool", "content": "Error: " + result["error"]})
            else:
                messages.append({"role": "tool",
                                 "content": json.dumps(result["value"], ensure_ascii=False)})
        return "达到最大步数仍未收敛，需要 compaction 或人工介入"

    def execute(self, call, messages):
        name, args = call["name"], call.get("arguments", {})
        # 把模型发出的调用原样记入历史，保证对话上下文完整
        messages.append({"role": "assistant",
                         "content": "call " + name + " " + json.dumps(args, ensure_ascii=False)})
        tool = self.tools.get(name)
        if tool is None:
            return {"error": "unknown tool: " + name, "value": None}
        try:
            return {"error": None, "value": tool.func(**args)}
        except Exception as e:
            # 参数类型错、越界、超时等异常全部回灌，而不是直接崩掉
            return {"error": type(e).__name__ + ": " + str(e), "value": None}
```

### 上下文压缩与 subagent

```python
COMPACT_PROMPT = "把以下对话压缩成简明摘要，保留关键结论、已获取的工具结果和待办事项："

def compact(messages, llm, keep_recent=4):
    # 上下文压缩：老消息整段摘要成一条 system 消息，最近几轮保留原文。
    if len(messages) <= keep_recent + 2:
        return messages
    old, recent = messages[:-keep_recent], messages[-keep_recent:]
    summary = llm.chat([{"role": "user", "content": COMPACT_PROMPT + str(old)}])
    return [{"role": "system", "content": "历史摘要: " + summary}] + recent


class SubAgent:
    # 子任务独立上下文 + 独立步数上限，主 agent 只拿最终结论（对标 Claude Code 的 Task 工具）。

    def __init__(self, llm, tools, name, max_steps=4):
        self.name = name
        self.loop = AgentLoop(llm, tools, max_steps=max_steps)

    def run(self, task):
        return self.loop.run("你是子任务执行者 " + self.name + "，任务: " + task)


def delegate(sub_task):
    # 把 subagent 包装成主 agent 的一个"工具"，主循环通过它派发子任务
    return SubAgent(LLM, TOOLS, "researcher").run(sub_task)

register_tool(delegate)


class FakeLLM:
    # 演示用假客户端，接口与真实 chat completion 一致。
    # 真实实现：本地用 transformers 的 AutoModelForCausalLM + chat template 生成，
    # 或调用 OpenAI-compatible API；关键是 tools 参数按 function calling 格式传入。

    def __init__(self, script):
        self.script, self.i = script, 0

    def chat(self, messages, tools=None):
        self.i += 1
        return self.script[min(self.i - 1, len(self.script) - 1)]


# 剧本：第一步调 add 工具，第二步给出最终答案
LLM = FakeLLM([
    {"type": "tool_call", "tool_call": {"name": "add", "arguments": {"a": 12, "b": 30}}},
    {"type": "final_answer", "text": "12 + 30 = 42"},
])
```

## 深挖追问

**Q1：工具为什么要 schema 化，写进 prompt 让模型自由输出 JSON 不行吗？**
自由文本解析有三个问题：格式不稳定（模型可能加解释文字、换行、用错引号）、无法校验参数类型、出错后没法定位是"模型写错了"还是"工具坏了"。schema 让模型在训练中见过结构化输出的监督信号，输出可解析、可校验的 tool_call；服务端还能用 schema 先做参数约束（如范围检查）再传给工具，安全边界更清晰。

**Q2：错误回灌的价值在哪，不会把模型带偏吗？**
一个工具调用失败时不回灌、直接 abort，任务就死了；回灌报错后模型通常能自己改参数重试（把 str 改成 int、换个工具名）。风险是死循环——所以要有 max_steps 和单工具重试上限，超限后降级：换工具、给候选方案、或转人工。错误回灌 + 重试上限 + 降级路径，三层一起讲才是完整答案。

**Q3：compaction 什么时候触发，怎么做信息损失最小？**
触发条件一般按 token 阈值（如超过上下文窗口的 80%）或步数阈值。最简单的是整段摘要 + 保留最近 k 轮；更好的是结构化 compaction：按"已完成任务、关键结论、待办、失败记录"分字段总结，信息密度高且稳定。生产系统还配合工具返回截断（长网页只留相关片段）一起控上下文。

**Q4：和 Claude Code / Codex CLI 的设计点怎么逐一映射？**
- system prompt 分层：全局规则 / 项目规则（AGENTS.md）/ 工具说明分块注入，本项目的 SYSTEM_PROMPT 是单层最简版；
- 工具注册表：对应其 tools 数组，schema 自动生成、描述参与提示构造；
- 主循环：对应其 agentic loop 的 step 控制与 max_turns；
- compaction：对应其上下文自动压缩与历史管理；
- subagent：对应 Claude Code 的 Task 工具 / Codex CLI 的 subagent，隔离上下文、只回传结论；
- 权限：生产级还有 tool 级审批（写文件、执行命令前确认），本项目未实现但可作为加分延伸。

**Q5：步数上限和上下文长度哪个先爆，怎么权衡？**
每步都要追加一条 assistant 消息 + 一条工具结果，长任务上下文先爆。所以工程上三管齐下：工具返回截断（限制字节数）、compaction（旧消息摘要化）、subagent（把细节消化在子上下文里）。max_steps 更多是防死循环的保险，不是主约束。

## 面试加分点

- 把"工具 = schema + 描述 + 函数"三层结构讲清楚，面试官问"工具调用是怎么实现的"直接有答案；
- 错误回灌讲到"模型自纠错 + 重试上限 + 降级路径"三层，展示工程兜底意识；
- 能画出一张与 Claude Code 的映射表（prompt 分层 / 工具集 / 循环 / compaction / subagent / 权限），证明研究过生产系统；
- 提到 harness 与模型的解耦：换底层 LLM 不改循环逻辑，评估时同一套 harness 跑不同模型做对比。''',
    },
    {
        "id": "proj-008",
        "name": "OpenVLA 式动作离散化 VLA 骨架",
        "domain": "embodied",
        "level": "前沿",
        "tags": ["VLA", "具身智能"],
        "summaryMd": r'''实现 OpenVLA 式 VLA 骨架：视觉编码器（占位 DINOv2/SigLIP）+ projector + 预训练 LLM，把 7 维机械臂动作离散化成每维 256 bins 的动作 token，用 LM 头输出并反离散化执行，附带 action chunking 与 LoRA 微调策略。面试讲这个项目最加分的是：说清"为什么动作要离散化"与"推理频率跟不上控制频率怎么办"这两个具身方向最常考的问题。''',
        "bodyMd": r'''## 背景与思路

VLA（Vision-Language-Action）要解决的核心问题是：把视觉观测和语言指令映射成机械臂动作。OpenVLA（Stanford/UC Berkeley, 2024）给出的答案是"把 VLM 当策略"：在 7B 的 Prismatic VLM 上微调，动作输出用离散化的 action token 表示——7 维动作（Δx, Δy, Δz, Δroll, Δpitch, Δyaw, gripper）每维离散成 256 个 bin，预测动作就变成"在词表后追加的 7×256 个 token 上做分类"，与文本 token 共用同一套训练和推理基础设施。

选择离散化而不是直接回归连续值的直觉有三条：一是统一词表，动作 token 与文本 token 在同一 embedding 空间，预训练先验可以直接复用；二是分类训练在数据少时比回归稳（回归对异常值敏感，且动作分布是多峰的——同一条指令有多种合法动作，MSE 会学出"平均动作"）；三是复用 LLM 的全部工程（采样、温度、并行推理）。

另一个必须面对的现实是频率：LLM 一次前向几百毫秒，而机械臂控制通常要 10-50Hz 的反馈。解法是 action chunking——一次推理输出未来 k 步动作，执行期间并行做下一次推理；同时视觉 token 在观测不变时只需编码一次。

## 架构设计

数据流：相机图像 → 冻结的视觉编码器（占位 DINOv2/SigLIP，输出 patch 特征）→ projector 升维到 LLM 维度 → 与指令文本 embedding 拼接 → LLM 前向 → 动作头（输出 7×256 个 logits）→ 每维 argmax 得 7 个离散 token → 反离散化得到连续动作。训练时只在动作输出位置算逐维交叉熵，文本位置 mask 掉；微调时冻结 LLM 主干挂 LoRA，projector 和动作头全参训练。

## 关键组件实现

### 动作离散化与反离散化

```python
import numpy as np

ACTION_DIM = 7        # x, y, z, roll, pitch, yaw, gripper
ACTION_BINS = 256     # 与 OpenVLA 一致：每维 256 bins
# 每维归一化边界；真实实现用训练集动作的分位数统计做逐维归一化
LOW = np.array([-0.1, -0.1, -0.1, -np.pi, -np.pi, -np.pi, 0.0])
HIGH = np.array([0.1, 0.1, 0.1, np.pi, np.pi, np.pi, 1.0])

def discretize(actions):
    # 连续动作 -> [0, 255] 的整数 token：先 clip 再线性映射到 bins。
    a = np.clip(actions, LOW, HIGH)
    norm = (a - LOW) / (HIGH - LOW)         # 逐维归一化到 [0, 1]
    return np.round(norm * (ACTION_BINS - 1)).astype(np.int64)

def undiscretize(tokens):
    # 离散 token -> 连续动作：取 bin 中心，即 (t + 0.5) / 256 再反归一化。
    t = np.clip(tokens, 0, ACTION_BINS - 1).astype(np.float32)
    norm = (t + 0.5) / ACTION_BINS
    return norm * (HIGH - LOW) + LOW
```

### VLA 骨架

```python
import torch
import torch.nn.functional as F

class VisionEncoder(torch.nn.Module):
    # 占位实现。真实项目用 transformers 加载冻结编码器，例如：
    # AutoModel.from_pretrained("facebook/dinov2-base") 或 SigLIP，
    # 输出 (B, N_patch, D)。这里用可学习 patch embedding 代替，接口一致。

    def __init__(self, dim=768, patch=14, img=224):
        super().__init__()
        self.num_patches = (img // patch) ** 2
        self.proj = torch.nn.Conv2d(3, dim, kernel_size=patch, stride=patch)

    def forward(self, imgs):
        x = self.proj(imgs)                     # (B, D, H/patch, W/patch)
        return x.flatten(2).transpose(1, 2)     # (B, N_patch, D)


class VLAModel(torch.nn.Module):
    # OpenVLA 式骨架：视觉 token + 指令 token 拼进 LLM，动作头输出 bins*7 个 logits。

    def __init__(self, llm, vision_dim=768, llm_dim=4096, bins=256, action_dim=7):
        super().__init__()
        self.llm = llm                      # 预训练 LLM（真实模型：Prismatic/LLaMA-2 7B）
        self.bins, self.action_dim = bins, action_dim
        self.vision = VisionEncoder(dim=vision_dim)
        self.projector = torch.nn.Linear(vision_dim, llm_dim)   # 视觉 -> LLM 维度
        self.action_head = torch.nn.Linear(llm_dim, bins * action_dim)

    def forward(self, imgs, text_ids, text_mask):
        vis_tok = self.projector(self.vision(imgs))              # (B, N_patch, llm_dim)
        text_emb = self.llm.get_input_embeddings()(text_ids)
        inputs = torch.cat([text_emb, vis_tok], dim=1)           # 指令在前，视觉在后
        attn_mask = torch.cat([
            text_mask,
            torch.ones(vis_tok.shape[0], vis_tok.shape[1], device=imgs.device),
        ], dim=1)
        hidden = self.llm(inputs_embeds=inputs, attention_mask=attn_mask).last_hidden_state
        return self.action_head(hidden)                          # (B, L, bins * 7)


def action_loss(logits, action_tokens, action_pos):
    # 在动作输出位置逐维算 256 分类交叉熵；action_pos 是最后一个 token 的位置。
    B = logits.shape[0]
    logits = logits[torch.arange(B), action_pos].view(B, 7, -1)   # (B, 7, bins)
    return F.cross_entropy(logits.transpose(1, 2), action_tokens) # 目标 (B, 7)
```

### action chunking 与 LoRA 微调

```python
def predict_action_chunk(model, imgs, text_ids, text_mask, chunk_len=5):
    # 一次推理输出未来 chunk_len 步动作：LLM 慢、控制快，用 chunking 填补频率缺口。
    logits = model(imgs, text_ids, text_mask)[:, -chunk_len:]     # (B, chunk_len, bins*7)
    tokens = logits.view(-1, 7, 256).argmax(dim=-1)               # 每维独立 argmax
    return undiscretize(tokens.detach().cpu().numpy())            # (B*chunk_len, 7)


class LoRALinear(torch.nn.Module):
    # 低秩旁路：y = Wx + (alpha/r) * B A x。A 高斯初始化、B 零初始化，
    # 保证训练起点严格等价原模型，冻结的 W 不产生梯度。

    def __init__(self, linear, r=16, alpha=32):
        super().__init__()
        self.linear = linear
        for p in self.linear.parameters():
            p.requires_grad = False
        self.A = torch.nn.Parameter(torch.randn(r, linear.in_features) * 0.02)
        self.B = torch.nn.Parameter(torch.zeros(linear.out_features, r))
        self.scale = alpha / r

    def forward(self, x):
        return self.linear(x) + self.scale * (x @ self.A.T @ self.B.T)


def attach_lora(llm, r=16):
    # 只给 q/k/v/o 投影挂 LoRA（OpenVLA 的实践：挂 attention 投影性价比最高）。
    for name, child in list(llm.named_modules()):
        if isinstance(child, torch.nn.Linear) and name.split(".")[-1] in (
                "q_proj", "k_proj", "v_proj", "o_proj"):
            parent = llm
            for part in name.split(".")[:-1]:
                parent = getattr(parent, part)
            setattr(parent, name.split(".")[-1], LoRALinear(child, r=r))
    return llm
```

## 深挖追问

**Q1：离散化和直接回归连续值，各自的取舍？**
离散化：训练稳、复用 LLM 基础设施、能表达多峰分布（256 个 logits 可以学出两个峰），代价是精度被 bin 量化、词表膨胀。回归：输出连续无损，但 MSE 损失隐含高斯单峰假设，动作多峰时学出"两个可行点的平均位置"，数据少时极易过拟合。π0 用流匹配（flow matching）在连续空间建模多峰分布，是第三条路线。

**Q2：256 bins 的精度够吗？**
按 OpenVLA 的逐维归一化，位置维 bin 宽约 1 毫米、旋转维约 0.02 rad，配合闭环重规划（每次观测后重新推理），精度足够抓取级任务。bin 数翻倍词表就翻倍，训练难度和显存上升，256 是精度与成本的平衡点，也是与文本 tokenizer 词表量级对齐的选择。

**Q3：LLM 推理慢，控制要 10-50Hz，怎么解决？**
三层答案：1) action chunking，一次推理出未来 k 步（如 5 步），执行期间并行做下一次推理，等效频率 = chunk 长度 × 推理频率；2) 分层控制，π0 的做法是流匹配在 50Hz 高频生成动作、VLM 在 1Hz 低频给语义目标，两路融合；3) 工程压缩：量化、小模型蒸馏、缓存视觉 token（观测不变时只重算文本侧）。面试讲清 chunking 的延迟/精度权衡即可过关。

**Q4：为什么用预训练 LLM 权重初始化，而不是从零训一个小模型？**
VLA 数据以万级 episode 计，从零训会严重过拟合；LLM 预训练带来指令跟随、常识与开放词汇理解，RT-2 和 OpenVLA 都验证了 web 知识的正迁移。代价是 7B 推理慢、显存大，所以后来有 TinyVLA、SmolVLA 等蒸馏/小型化版本，工业界也在训 1-3B 的专用 VLA。

**Q5：LoRA 挂在哪、为什么冻结视觉编码器？**
OpenVLA 实践：LLM 的 q/k/v/o 投影挂 LoRA（attention 层对行为影响最大且参数量可控），projector 和动作头全参训练（它们是新增的随机初始化模块，必须全训）。视觉编码器冻结是为了保留预训练特征并省显存；数据量足够大时也可以解冻最后几层或全量微调。

## 面试加分点

- 说出"离散化 = 统一词表 + 分类更稳 + 复用 LLM 工程"三条理由，而不是只会背"256 bins"；
- 频率问题的三层解法（chunking / 分层控制 / 工程压缩）能张口就来，这是具身面试最高频追问；
- 讲清训练时只有动作位置算 loss、文本位置 mask 掉，体现对 VLM 训练细节的理解；
- 主动对比 OpenVLA（离散 token）、π0（流匹配连续）、Diffusion Policy（扩散），展示视野。''',
    },
    {
        "id": "proj-009",
        "name": "BEV 感知简化 Pipeline（LSS 思想）",
        "domain": "driving",
        "level": "进阶",
        "tags": ["自动驾驶", "BEV"],
        "summaryMd": r'''实现 LSS（Lift-Splat-Shoot）思想的 BEV 感知简化 pipeline：多相机特征 → 每像素深度分布 → 视锥特征池化到 BEV 网格 → 接检测头，含视锥构建、相机到自车坐标变换与求和池化的完整代码。面试讲这个项目最加分的是：能用一句话讲清 Lift 和 Splat 各自在做什么，并对比出 BEVFormer 注意力路线为什么数据效率更低。''',
        "bodyMd": r'''## 背景与思路

自动驾驶的多相机感知面临一个问题：每台相机看到的是自己的透视视图，物体在图像里会因距离、角度严重变形，而下游的预测和规划却需要一个统一的、以自车为中心的表征。BEV（Bird's Eye View，鸟瞰图）就是答案：把所有相机的信息投影到自车系地面网格上，检测、轨迹预测、规划共享同一张图。

LSS（Lift, Splat, Shoot，Philion & Fidler, ECCV 2020）开创了"显式几何投影"路线：Lift——每个像素不预测一个深度值，而是预测一条深度分布（D 个 bin 的概率），像素特征与深度分布外积得到视锥特征；Splat——视锥里的每个点按相机外参变换到自车坐标，离散化到 BEV 网格，同一格子的特征求和池化；Shoot 指基于 BEV 做未来路径规划，本骨架只做感知部分。

关键直觉：单目图像的深度本质是不适定问题（一个像素可能来自任意深度的物体），所以不做硬性单值预测，而是用分布把不确定性沿射线铺开，让可学习特征自己加权——这是 LSS 与"先深度估计再投影"两步法的本质区别。

## 架构设计

pipeline 分四段：共享 backbone（占位，真实项目用 ResNet/EfficientNet，多相机共享权重）→ Lift 头（两个 1×1 卷积分别出 D 维深度分布和 C 维特征，外积）→ Splat（视锥坐标变换 + 网格离散化 + scatter-add 池化）→ BEV 网格接检测头（占位，真实项目用 CenterPoint 风格的 2D 卷积头输出物体框/速度/朝向）。视锥坐标只依赖相机内外参，离线算一次缓存即可，推理时零开销。

## 关键组件实现

### 视锥构建与坐标变换

```python
import numpy as np

def make_frustum(W, H, D, fx, fy, near, far):
    # 生成像素视锥：每个 (u, v, d) 组合对应一条射线上的相机系 3D 点。
    u, v = np.meshgrid(np.arange(W, dtype=np.float32),
                       np.arange(H, dtype=np.float32))          # (H, W)
    depth = np.linspace(near, far, D, dtype=np.float32)         # (D,)
    # 针孔模型反投影：x = (u - cx) * d / fx；这里 cx, cy 取图像中心
    x = (u - W / 2.0)[..., None] * depth[None, None, :] / fx    # (H, W, D)
    y = (v - H / 2.0)[..., None] * depth[None, None, :] / fy
    z = np.broadcast_to(depth[None, None, :], (H, W, D))
    return np.stack([x, y, z], axis=-1)                          # (H, W, D, 3)


def cam_to_ego(points, rot, trans):
    # 相机系 -> 自车系：先旋转后平移。points: (..., 3), rot: (3, 3), trans: (3,)
    return points @ rot.T + trans


def build_frustums(cameras):
    # 按相机标定离线算好各相机的视锥点（自车系），推理时零开销复用。
    frus = []
    for cam in cameras:   # cam: dict(W, H, D, fx, fy, near, far, rot, trans)
        pts = make_frustum(cam["W"], cam["H"], cam["D"], cam["fx"], cam["fy"],
                           cam["near"], cam["far"])
        frus.append(cam_to_ego(pts, cam["rot"], cam["trans"]))
    return frus
```

### Lift：深度分布 × 特征

```python
import torch

class Lift(torch.nn.Module):
    # Lift：每个像素出 D 维深度分布和 C 维上下文特征，外积铺满整条视锥。

    def __init__(self, in_channels, out_channels, D):
        super().__init__()
        self.D = D
        self.depth_conv = torch.nn.Conv2d(in_channels, D, kernel_size=1)
        self.feat_conv = torch.nn.Conv2d(in_channels, out_channels, kernel_size=1)

    def forward(self, feats):
        # feats: (B, C_in, H, W)
        depth = torch.nn.functional.softmax(self.depth_conv(feats), dim=1)  # (B, D, H, W)
        ctx = self.feat_conv(feats)                                          # (B, C, H, W)
        # 外积：特征在每个深度 bin 上复制并乘以该 bin 的概率，不确定性沿射线铺开
        return torch.einsum("bdhw,bchw->bcdhw", depth, ctx)                  # (B, C, D, H, W)
```

### Splat：离散化 + 求和池化

```python
def splat(frustum_feats, frustum_pts, bev_h, bev_w, xbins, ybins):
    # Splat：视锥点（自车系）按坐标离散化，同一 BEV 格子的特征求和池化。
    B, C, D, H, W = frustum_feats.shape
    pts = frustum_pts.view(B, -1, 3)                          # (B, HWD, 3) 自车系坐标
    # 特征 (B,C,D,H,W) 重排成 (B,C,H,W,D) 再展平，与 pts 的 (h,w,d) 展开顺序逐点对齐
    flat = frustum_feats.permute(0, 1, 3, 4, 2).reshape(B, C, -1)   # (B, C, HWD)
    ix = torch.floor((pts[..., 0] - xbins[0]) / (xbins[1] - xbins[0]) * bev_w).long()   # x -> 网格列
    iy = torch.floor((pts[..., 1] - ybins[0]) / (ybins[1] - ybins[0]) * bev_h).long()   # y -> 网格行
    keep = (ix >= 0) & (ix < bev_w) & (iy >= 0) & (iy < bev_h)        # 范围外丢弃
    bev = torch.zeros(B, C, bev_h * bev_w, device=frustum_feats.device)
    for b in range(B):
        m = keep[b]
        ii = iy[b][m] * bev_w + ix[b][m]                     # 一维化网格索引
        idx = ii.unsqueeze(0).expand(C, ii.numel())          # 每个特征通道同一索引
        bev[b].scatter_add_(1, idx, flat[b][:, m])           # 同格多来源特征相加
    return bev.view(B, C, bev_h, bev_w)                       # BEV 特征图
```

### 深度监督与检测头

```python
import torch.nn.functional as F

BEV_H, BEV_W = 200, 200     # BEV 网格尺寸
XBINS = (-50.0, 50.0)       # 自车系 x 方向范围（米），每格 0.5m
YBINS = (-50.0, 50.0)

def depth_loss(depth_pred, depth_target):
    # LSS 的深度监督：LiDAR 点云投影到像素生成离散深度标签，做交叉熵。
    # depth_pred: (B, D, H, W) 预测分布；depth_target: (B, H, W) 标签，-1 表示无点云忽略。
    mask = depth_target >= 0
    ce = F.cross_entropy(depth_pred, depth_target.clamp(min=0), reduction="none")
    return ce[mask].mean()


class BEVPipeline(torch.nn.Module):
    # LSS 简化 pipeline：N 相机各自 lift，统一 splat 到 BEV，再上检测头。

    def __init__(self, out_channels, D, bev_h, bev_w):
        super().__init__()
        self.out_channels = out_channels
        self.bev_h, self.bev_w = bev_h, bev_w
        # 占位 backbone；真实项目换 ResNet/EfficientNet 且多相机共享权重
        self.backbone = torch.nn.Sequential(
            torch.nn.Conv2d(3, 64, 3, padding=1), torch.nn.ReLU())
        self.lift = Lift(64, out_channels, D)
        self.detect_head = torch.nn.Conv2d(  # 占位检测头，CenterPoint 风格
            out_channels, out_channels, 3, padding=1)

    def forward(self, imgs, frustums):
        # imgs: list[N] of (B, 3, H, W)；frustums: list[N] of (H, W, D, 3)
        B = imgs[0].shape[0]
        bev = torch.zeros(B, self.out_channels, self.bev_h, self.bev_w,
                          device=imgs[0].device)
        for img, frustum in zip(imgs, frustums):
            feats = self.lift(self.backbone(img))                 # (B, C, D, H, W)
            bev += splat(feats, frustum.unsqueeze(0).expand(B, -1, -1, -1, -1),
                         self.bev_h, self.bev_w, XBINS, YBINS)
        return self.detect_head(bev)
```

## 深挖追问

**Q1：LSS 的深度监督从哪来？**
训练时有 LiDAR：把点云投影到图像，每个有点的像素得到一个深度值，离散到 D 个 bin 作为 one-hot 标签，用交叉熵训练深度分布。没有点云的纯视觉部署路线拿不到直接监督，只能靠检测损失隐式学深度——这也是"LiDAR 数据决定 LSS 效果上限"说法的由来。

**Q2：和 BEVFormer 的注意力路线比，各自的取舍？**
LSS：显式几何投影，深度分布是强归纳偏置，数据效率高、训练快、可解释；但深度预测不准时特征被撒到错误格子，且深度分辨率受限。BEVFormer：BEV query 用可变形交叉注意力直接去各相机特征图上采样，几何关系靠学习而不是显式投影，上限更高、能端到端学；代价是收敛慢、数据需求大、跨相机时序对齐复杂。面试常用结论：数据少选 LSS 路线，数据充足选 BEVFormer 路线，量产系统常是两者的混合。

**Q3：视锥的显存和计算量怎么控制？**
视锥大小 H×W×D 是图像分辨率的 D 倍，D=128 时千万级点数，这是主要瓶颈。控制手段：降低 D（LSS 原文 D=41）、特征通道 C 取小（原文 64）、用 BEVPool 这类预计算索引的算子加速 splat（把 scatter-add 变成一次索引拷贝）、降低输入分辨率。工程直觉：BEV 200×200、每格 0.5m 是常用配置。

**Q4：splat 为什么用求和池化而不是 max？**
求和保留"多个相机看到同一物体"的证据累加，且可微性稳定；max 池化信息损失大（只留最强响应），训练中梯度只回传一个来源。求和的问题是遮挡/远处稀疏点会贡献噪声，所以有按深度置信度加权的改进版。

**Q5：多相机的重叠区域怎么处理？**
各相机独立 lift + splat，重叠区域的格子自然被多个相机的特征求和，等价于多视角投票。不需要显式的跨相机融合，这正是 LSS 简洁的地方——几何关系已经通过外参编码进视锥坐标了。

## 面试加分点

- 一句话讲清 Lift（深度分布铺射线）和 Splat（按坐标求和池化），面试官就能确认你真懂；
- 主动对比 LSS 与 BEVFormer 的数据效率/上限取舍，是 BEV 方向必问的送分题；
- 能报出 H×W×D 的显存量级和 BEVPool 加速思路，展示工程感；
- 把"深度分布"解释成"单目深度不适定的软化解"，而不是背公式。''',
    },
    {
        "id": "proj-010",
        "name": "视频世界模型骨架：VAE + 下一 latent 预测",
        "domain": "driving",
        "level": "前沿",
        "tags": ["世界模型", "生成模型"],
        "summaryMd": r'''搭建视频世界模型骨架：极简 VAE 把帧压缩到 latent，因果 transformer 在 latent 空间预测下一帧，自回归 rollout 生成未来视频，并支持动作条件。面试讲这个项目最加分的是：能讲清"为什么在 latent 空间预测"，并三句话分清 Sora（扩散）、Genie（动作条件下一帧）、V-JEPA（不重建像素）与本项目（自回归重建）的区别。''',
        "bodyMd": r'''## 背景与思路

世界模型的定义是：一个能预测环境未来状态的模型。对驾驶场景，输入是当前观测（多帧图像）和自车动作，输出是未来的观测——这正是自动驾驶闭环仿真梦寐以求的东西：一个便宜、可并行的"驾驶模拟器"，策略在其中试错不用碰真车。GAIA-1（Wayve）、DriveDreamer、UniSim 走的都是这条路。

直接预测像素有两个问题：像素空间维度高（64×64×3 ≈ 1.2 万维），且充满与任务无关的高频纹理噪声。所以主流做法分两步：VAE 先把单帧压缩到低维 latent（本项目 64×64×3 → 4×4×32，压缩比约 24 倍，真实系统用 8×8 空间压缩时更大），transformer 只学 latent 之间的动态。训练算力因此集中在"场景会怎么变"而不是"草叶子长什么样"。

与三个著名模型的边界：Sora 是在 latent 上做扩散生成（去噪过程采样，帧间无严格时序约束）；Genie 是动作条件下一帧预测 + 潜在动作发现（从视频无标签学动作）；V-JEPA 只预测未来表征、不重建像素（纯表征学习，避免低层信息浪费容量）。本骨架 = 自回归 + 连续 latent + 重建监督，属于 Genie/GAIA-1 风格。

## 架构设计

训练：帧序列 → VAE 编码（冻结 VAE 权重）→ 因果 transformer（当前 latent + 动作 embedding → 预测下一 latent，下三角 mask）→ MSE 损失 + VAE 的 KL/重建损失。推理：真实帧起手编码，自回归逐帧预测，滑动窗口控制上下文长度，最后 VAE 解码回像素得到生成视频。

## 关键组件实现

### 极简 VAE

```python
import torch
import torch.nn.functional as F

class ConvVAE(torch.nn.Module):
    # 帧级 VAE：64x64x3 -> 4x4x32 latent（压缩比约 24 倍），重建损失 + KL 训练。

    def __init__(self, latent_dim=32):
        super().__init__()
        self.encoder = torch.nn.Sequential(
            torch.nn.Conv2d(3, 32, 4, stride=2, padding=1),    # 32x32
            torch.nn.ReLU(),
            torch.nn.Conv2d(32, 64, 4, stride=2, padding=1),   # 16x16
            torch.nn.ReLU(),
            torch.nn.Conv2d(64, 128, 4, stride=2, padding=1),  # 8x8
            torch.nn.ReLU(),
            torch.nn.Conv2d(128, 256, 4, stride=2, padding=1), # 4x4
        )
        self.fc_mu = torch.nn.Conv2d(256, latent_dim, 1)       # 1x1 卷积出均值/方差
        self.fc_logvar = torch.nn.Conv2d(256, latent_dim, 1)
        self.decoder = torch.nn.Sequential(
            torch.nn.ConvTranspose2d(latent_dim, 256, 4, stride=2, padding=1),  # 8x8
            torch.nn.ReLU(),
            torch.nn.ConvTranspose2d(256, 128, 4, stride=2, padding=1),         # 16x16
            torch.nn.ReLU(),
            torch.nn.ConvTranspose2d(128, 64, 4, stride=2, padding=1),          # 32x32
            torch.nn.ReLU(),
            torch.nn.ConvTranspose2d(64, 3, 4, stride=2, padding=1),            # 64x64x3
        )

    def encode(self, x):
        h = self.encoder(x)
        return self.fc_mu(h), self.fc_logvar(h)

    def reparameterize(self, mu, logvar):
        # 重参数化技巧：让采样可导，VAE 才能端到端训练
        std = torch.exp(0.5 * logvar)
        return mu + torch.randn_like(std) * std

    def forward(self, x):
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        return self.decoder(z), mu, logvar


def vae_loss(x_hat, x, mu, logvar, beta=0.1):
    # beta < 1 弱化 KL，避免 posterior collapse（encoder 无视输入、输出常数）
    rec = F.mse_loss(x_hat, x)
    kl = -0.5 * (1 + logvar - mu.pow(2) - logvar.exp()).sum(dim=(1, 2, 3)).mean()
    return rec + beta * kl
```

### 因果 transformer 预测下一 latent

```python
class NextLatentTransformer(torch.nn.Module):
    # 因果 transformer：输入 t 帧 latent + 动作，输出对 t+1 帧 latent 的预测。

    def __init__(self, latent_dim=32, d_model=256, n_heads=4, n_layers=4,
                 max_frames=32, act_dim=2):
        super().__init__()
        self.max_frames = max_frames
        self.pos_embed = torch.nn.Parameter(torch.randn(1, max_frames, d_model))
        self.in_proj = torch.nn.Linear(latent_dim * 4 * 4, d_model)
        self.action_embed = torch.nn.Linear(act_dim, d_model)   # 动作条件：转角/油门
        layer = torch.nn.TransformerEncoderLayer(
            d_model=d_model, nhead=n_heads, dim_feedforward=1024, batch_first=True)
        self.blocks = torch.nn.TransformerEncoder(layer, num_layers=n_layers)
        self.out_proj = torch.nn.Linear(d_model, latent_dim * 4 * 4)

    def forward(self, latents, actions=None):
        # latents: (B, T, C, 4, 4)；位置 t 的输出预测 z_{t+1}
        B, T = latents.shape[0], latents.shape[1]
        x = self.in_proj(latents.flatten(2))                    # (B, T, d_model)
        if actions is not None:
            # 动作条件加到输入侧：预测 z_{t+1} 时可看到 a_t（GAIA-1 同思路）
            x = x + self.action_embed(actions)
        x = x + self.pos_embed[:, :T]
        causal = torch.triu(torch.ones(T, T, dtype=torch.bool, device=latents.device),
                            diagonal=1)                          # 只能看过去（True=禁止注意）
        h = self.blocks(x, mask=causal)
        return self.out_proj(h).view(B, T, -1, 4, 4)


def world_model_loss(model, vae, frames):
    # 冻结 VAE 编码，用前 T-1 帧预测后 T-1 帧的 latent（位移一位对齐）。
    with torch.no_grad():
        B, T = frames.shape[:2]
        mu, logvar = vae.encode(frames.flatten(0, 1))   # (B*T, 3, 64, 64) 逐帧编码
        z = vae.reparameterize(mu, logvar).view(B, T, -1, 4, 4)
    pred = model(z)
    return F.mse_loss(pred[:, :-1], z[:, 1:])     # teacher forcing 训练
```

### rollout 生成

```python
def rollout(model, vae, first_frames, n_steps, temp=0.8, window=16):
    # 自回归 rollout：真实帧起手，之后每步喂模型自己预测的 latent（误差会累积）。
    with torch.no_grad():
        B, T0 = first_frames.shape[:2]
        mu = vae.encode(first_frames.flatten(0, 1))[0]      # (B*T0, 3, 64, 64) 逐帧编码
    z = mu.view(B, T0, -1, 4, 4).detach()          # 用 mu 作起始，保证确定性
    zs = [z]
    cur = z
    for _ in range(n_steps):
        with torch.no_grad():
            next_z = model(cur)[:, -1:]            # 当前窗口预测下一帧
            if temp > 0:
                next_z = next_z + torch.randn_like(next_z) * temp   # 温度控制多样性
        zs.append(next_z)
        cur = torch.cat([cur[:, 1:], next_z], dim=1)   # 滑动窗口，上下文不无限增长
        if cur.shape[1] > window:
            cur = cur[:, -window:]
    zs_all = torch.cat(zs, dim=1)                  # (B, T_total, C, 4, 4) 全部 latent 帧
    B, T = zs_all.shape[:2]
    frames = vae.decoder(zs_all.flatten(0, 1))     # 解码器输入 (B*T, C, 4, 4) -> (B*T, 3, 64, 64)
    return frames.view(B, T, *frames.shape[1:])    # 还原成 (B, T, 3, 64, 64) 的视频
```

## 深挖追问

**Q1：为什么在 latent 空间预测而不是像素空间？**
三个理由：1) 降维——64×64×3 压到 4×4×32，transformer 的序列长度和计算量大幅下降；2) 去噪——VAE 天然丢弃高频纹理，transformer 容量集中在语义动态上；3) 生成质量——解码器把模糊的 latent 预测重建成清晰帧，像素级 MSE 的"平均模糊"问题被 VAE 吸收。代价是 VAE 压缩有信息损失，细节（远处小目标、车牌）可能重建不出。

**Q2：与 Sora、Genie、V-JEPA 的区别？**
Sora：latent 空间做扩散（patch 化 + DiT），去噪迭代采样，用文本/条件引导，帧数多画质高，但推理慢、不是严格按因果动态生成。Genie：动作条件下一帧预测 + 潜在动作模型（从视频无标签学出离散动作），强调可交互。V-JEPA：联合嵌入预测表征，不重建像素，纯自监督表征学习，不是生成模型。本项目：自回归 + 连续 latent + 重建监督，最接近 Genie/GAIA-1 一侧，特点是能加自车动作做条件、计算量小。

**Q3：怎么把它用于驾驶闭环仿真？**
把世界模型当作"可交互环境"：策略输出自车动作 → 动作 embedding 条件进 transformer → 生成未来多帧观测 → 回喂策略，构成闭环训练。价值：仿真帧率远高于物理渲染、场景可以从真实数据扩展（改变初始帧/动作分布做反事实数据增强）、评测策略时能生成"如果当时换条路线会怎样"的反事实视频。工程前提：生成的观测要足够一致（语义、物体位置、物理合理性），否则策略学的是幻觉。

**Q4：自回归 rollout 的误差累积怎么办？**
根本矛盾：训练时 teacher forcing 喂真实 latent，推理时喂自己预测的 latent，误差逐帧放大（exposure bias）。缓解手段：1) teacher forcing 比例调度（训练中随机用上一步预测替代真实帧）；2) 推理时周期性用真实观测重置窗口；3) 缩短 rollout 长度、控制采样温度；4) 训练时给 latent 加噪，让模型对不完美输入鲁棒。

**Q5：VAE 的 KL 权重和 posterior collapse 是什么？**
posterior collapse 指 KL 项把 encoder 压成与输入无关的先验，模型退化成"背模板生成"，latent 失去信息量。对策：beta < 1 弱化 KL、KL 退火（训练中逐步加大权重）、或换 VQ-VAE（离散 codebook，没有 KL 项）。Sora 用的就是 VQ 风格、带 EMA 的 VAE，工程上更稳。

## 面试加分点

- 把"latent 空间预测"的三个理由（降维/去噪/重建质量）讲成因果链，而不是罗列；
- 四模型对比（Sora/Genie/V-JEPA/本项目）用"生成方式 × 动作条件 × 是否重建"三个轴组织，清晰且有记忆点；
- 主动提 exposure bias 与 teacher forcing 调度的矛盾，展示训练过生成模型的实战感；
- 把世界模型落到"驾驶闭环仿真 + 反事实数据增强"的具体价值，而非停留在"预测未来视频"。''',
    },
]

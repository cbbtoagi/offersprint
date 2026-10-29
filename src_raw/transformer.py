# -*- coding: utf-8 -*-
# Transformer与大模型结构题库（纯数据文件，顶部不 import）
# 覆盖：Attention机制 / 注意力变体 / 位置编码 / 结构细节 / KVCache与推理优化 / MoE / 显存与计算量估算 / 结构前沿

QUESTIONS = [
    # ---------------------------------------------------------------- Attention机制
    {
        "id": "transformer-001",
        "topic": "Attention机制",
        "type": "八股",
        "difficulty": 2,
        "frequency": 5,
        "companies": ["字节", "阿里", "腾讯", "百度"],
        "years": ["2023", "2024", "2025"],
        "question": "讲一下 Self-Attention 里 Q、K、V 各自的角色，为什么点积之后要除以根号 d_k？",
        "answerMd": r'''**一句话核心**：Q/K/V 是把同一份输入投影成「查询、键、值」三种角色做可学习的软寻址，除以 $\sqrt{d_k}$ 是为了控制点积方差、防止 softmax 饱和导致梯度消失。

**1. 三个投影的角色。** 输入 $x$ 经三个权重矩阵得到 $Q = xW_Q$、$K = xW_K$、$V = xW_V$。注意力分数 $s_{ij} = q_i \cdot k_j$ 衡量「第 i 个位置的查询与第 j 个位置的键有多匹配」，softmax 后得到权重，对 $v_j$ 加权求和。直观理解是一次可微分的字典查询：Q 是问题，K 是索引，V 是内容。若 Q、K、V 不加投影直接用同一个向量，注意力矩阵退化为 $\mathrm{softmax}(xx^\top)$，关于输入对称且不可学习路由，表达能力大打折扣。

**2. 为什么要缩放。** 假设 $q, k$ 的各分量独立、均值 0 方差 1，则点积 $q \cdot k = \sum_{t=1}^{d_k} q_t k_t$ 的方差是 $d_k$。维度越大点积绝对值越大，softmax 会趋近 one-hot：最大项概率接近 1，其余接近 0，此时 softmax 的梯度 $\mathrm{diag}(p) - pp^\top$ 趋近 0，反向传播几乎断流。除以 $\sqrt{d_k}$ 把方差拉回 1，让 logits 保持温和尺度。它本质上就是温度 $T = \sqrt{d_k}$ 的 softmax。

**3. 补充。** 实现中先算 $QK^\top$（可加 causal mask）再 softmax 再乘 $V$；$\sqrt{d_k}$ 是经验的标准答案，部分工作还会用可学习温度或对 Q/K 做 Norm 来进一步控制 logits 尺度。''',
        "keyPoints": [
            "Q 是查询、K 是索引、V 是内容，注意力是可微分的软寻址",
            "不加投影时注意力矩阵是 xx^T 的 softmax，对称且路由不可学习",
            "点积方差为 d_k，不缩放会使 softmax 趋近 one-hot、梯度消失",
            "除以 sqrt(d_k) 等价于温度 softmax，把 logits 方差归一到 1",
        ],
        "followUps": [
            {"q": "为什么用点积而不是加性注意力？", "a": r"点积可以写成矩阵乘 $QK^\top$，高度依赖 GEMM、算得快；加性注意力（如 Bahdanau）要多一层 MLP 逐对打分，复杂且慢。论文结论是两者在 $d_k$ 适中时效果相当，点积配合缩放即可。"},
            {"q": "缩放因子换成 1/d_k 会怎样？", "a": "缩放过头，logits 方差变成 1/d_k，softmax 输出过于平坦、接近均匀分布，注意力失去区分度，等价于温度过高。sqrt(d_k) 恰好把方差归一。"},
        ],
    },
    {
        "id": "transformer-002",
        "topic": "Attention机制",
        "type": "八股",
        "difficulty": 3,
        "frequency": 5,
        "companies": ["字节", "阿里", "百度", "华为"],
        "years": ["2023", "2024", "2025"],
        "question": "算一下标准 Transformer 一层的参数量与计算量，为什么说序列长度是自注意力的瓶颈？",
        "answerMd": r'''**一句话核心**：一层 Transformer 约有 $12d^2$ 参数、每 token 每层约 $24d^2$ FLOPs，其中注意力部分自带 $O(n^2 d)$ 的序列平方项，这是长上下文的根本瓶颈。

**1. 参数量。** 设隐层宽度为 $d$、FFN 隐层 $4d$：注意力有 $W_Q, W_K, W_V, W_O$ 四个 $d \times d$，共 $4d^2$；FFN 两个矩阵 $d \times 4d$ 与 $4d \times d$ 共 $8d^2$；合计约 $12d^2$（LN、bias 忽略）。用 SwiGLU 的现代模型把 FFN 隐层改为 $\frac{8}{3}d$、三个矩阵，总参数仍是约 $12d^2$ 量级。

**2. 计算量（每层每 token，乘加各算一次 FLOP）。** 投影矩阵：$Q/K/V/O$ 各 $2d^2$，共 $8d^2$；FFN 约 $16d^2$（或 SwiGLU 下对齐），合计约 $24d^2$ FLOPs/token；整层 $L$ 层模型对长度 $n$ 的序列为 $O(L \cdot n \cdot d^2)$，即参数线性项。

**3. 注意力的平方项。** $QK^\top$ 与 $AV$ 各是 $n \times n \times d_k$ 的矩阵乘，每层 $2 \cdot 2 n^2 d_k = 4n^2d$ FLOPs；中间的注意力矩阵本身是 $n \times n$，朴素实现要在显存里物化它。当 $n < d$ 时平方项可忽略，但上下文到 32K、128K 时 $n^2$ 项主导：显存 $O(n^2)$、计算 $O(n^2d)$，训练和推理都不可承受。

**4. 应对方向。** 这正是 FlashAttention（减少 IO 而非 FLOPs）、稀疏/滑窗/线性注意力、KV Cache 量化与分页管理、MoE 稀疏激活等一整套工作的出发点；面试时能顺着「平方项在哪、谁来救」这条线讲清即可。''',
        "keyPoints": [
            "一层参数约 4d^2(注意力) + 8d^2(FFN) = 12d^2",
            "每 token 每层 FLOPs 约 24d^2 量级，全模型 6ND 中的 N 与此对应",
            "注意力 logits 矩阵 O(n^2) 显存、O(n^2 d) 计算，n 大时主导总成本",
            "长上下文优化的两大方向：省 IO(FlashAttention) 与降复杂度(稀疏/线性)",
        ],
        "followUps": [
            {"q": "n 多大时注意力平方项开始主导？", "a": "比较 4n^2 d 与约 24 n d^2：当 n 约为 6d 时两者相当，d=4096 即 n 约两万多 token 时平方项开始占优。粗略说上下文超过一两万 token 后，注意力就是主要开销。"},
        ],
    },
    {
        "id": "transformer-003",
        "topic": "Attention机制",
        "type": "八股",
        "difficulty": 3,
        "frequency": 5,
        "companies": ["字节", "阿里", "美团", "快手"],
        "years": ["2023", "2024", "2025"],
        "question": "Transformer 里的 mask 有哪几种？分别加在哪个位置、取什么值，写代码时有哪些易错点？",
        "answerMd": r'''**一句话核心**：mask 分 padding mask（屏蔽 batch 内补齐位）和 causal mask（屏蔽未来位置），都加在 softmax 之前的 logits 上，用极大负数让该位置权重为 0。

**1. 加的位置。** mask 作用在 $QK^\top/\sqrt{d_k}$ 之后的 logits 上，softmax 之前。softmax 后再加没有意义（分布已归一化），加在输入 $x$ 上也无法表达「该位置不许被看见」。取值为 $-\infty$（实现中用 -1e4、-1e9 等大负数），softmax 后对应权重精确为 0。padding mask 屏蔽 key 侧的补齐 token（query 是真实 token 即可）；causal mask 取下三角 $\mathrm{tril}$，位置 $i$ 只能看见 $j \le i$。

**2. 易错点一：形状与广播。** padding mask 形状是 $(B, 1, 1, n_k)$，causal 是 $(1, 1, n, n)$，要与 $(B, h, n_q, n_k)$ 的 logits 广播相容；query 侧 padding 行全被 mask 时 softmax 分母为 0 产生 NaN，需要保证每行至少一个可见位或对该行输出置 0。

**3. 易错点二：位置编码与 packing。** 加了 mask 不等于「位置信息正确」：RoPE/位置 id 必须与真实 token 对齐（padding 位不能参与位置计数）；packing 把多个文档拼到一条序列时，若只用一个整体 causal mask，后面的文档会「看见」前面的文档（跨文档注意力污染），训练 LLM 时常用 varlen/文档内 attention mask 隔离。

**4. 推理侧。** 自回归解码用增量 causal mask（新 token 只看历史）；KV Cache 命中后每步只算一个 query 行，此时不再需要完整 $n \times n$ mask。''',
        "keyPoints": [
            "mask 加在 softmax 前的 logits 上，取极大负数使权重为 0",
            "padding mask 屏蔽 key 侧补齐位，causal mask 下三角防止看未来",
            "全 mask 行会导致 softmax 除 0 产生 NaN，要特殊处理",
            "packing 时需文档级 attention mask 隔离，防止跨文档注意力污染",
        ],
        "followUps": [
            {"q": "为什么用 -1e9 而不是真的 -inf？", "a": "真 -inf 在某些硬件/算子下会产生 NaN（-inf 减 -inf 或 0 乘 -inf），大负数即可让 exp 后为 0，数值上更安全。用 float('-inf') 配合稳定 softmax 也可，但要保证每行有非 mask 项。"},
            {"q": "cross-attention 里怎么用 mask？", "a": "decoder 对 encoder 输出做交叉注意力时，key 来自源序列，需要按源序列的 padding 加 padding mask；不存在因果 mask，因为源序列对 decoder 是完整可见的。"},
        ],
    },
    {
        "id": "transformer-004",
        "topic": "Attention机制",
        "type": "八股",
        "difficulty": 3,
        "frequency": 5,
        "companies": ["字节", "阿里", "腾讯", "月之暗面"],
        "years": ["2023", "2024", "2025"],
        "question": "多头注意力到底「多」出了什么能力？头数怎么选，是不是越多越好？",
        "answerMd": r'''**一句话核心**：多头把 $d$ 维空间切成 $h$ 个低维子空间，各自独立做注意力再拼接，让模型在不同子空间同时捕捉不同类型的关系；头数是「子空间多样性」与「单头维度充足」之间的权衡，并非越多越好。

**1. 多头带来什么。** 单头注意力只有一个 softmax 分布，所有位置的关系被压进一种打分模式。多头等价于 $h$ 套独立的 $(W_Q, W_K, W_V)$：不同头可以分别学句法依赖（如主谓）、位置临近性、指代、长程检索等不同模式，输出拼接后经 $W_O$ 线性融合。计算量与单大头基本相同（$h \cdot d_k = d$），换来的是模式多样性。

**2. 约束一：头不能太碎。** 有研究指出注意力存在低秩瓶颈：当单头维度 $d_k = d/h$ 过小时，softmax 注意力矩阵的秩受限、表达能力下降，因此常见做法限制 $d_k$ 不小于 64~128。这就是为什么 4096 宽的模型常用 32 头（$d_k=128$）而不是 128 头。

**3. 约束二：收益递减。** 同参数量下增加头数，验证损失往往先降后平甚至变差；头与头之间也存在冗余，剪枝研究发现相当比例的头可以去掉而不掉点（有些还充当「无操作」的寄存器/attention sink）。

**4. 工程视角。** 头数还影响 GQA/MQA 分组（KV 头数取值）、TP 切分（头要能整除 TP 度）与算子效率；现代 LLM 常用 $d_k \in [64, 128]$、头数 8~128 不等，属于与总宽度配套的结构超参。''',
        "keyPoints": [
            "多头 = h 个独立子空间的注意力再拼接，捕捉多种关系模式",
            "计算量与等宽单头几乎相同，h*d_k = d",
            "单头维度过小触发低秩瓶颈，d_k 一般不低于 64",
            "头数过多收益递减且存在冗余头，需与宽度、TP/GQA 约束一起定",
        ],
        "followUps": [
            {"q": "有没有头数可学习或自适应的方案？", "a": "有，如 Talk-to-head 类的注意力头剪枝与合并、可微架构搜索选头数；实际大模型里更多是在预训练后做结构化剪枝或干脆保持固定头数，训练时改动头数成本太高。"},
        ],
    },
    {
        "id": "transformer-005",
        "topic": "Attention机制",
        "type": "八股",
        "difficulty": 4,
        "frequency": 3,
        "companies": ["智谱", "月之暗面", "DeepSeek"],
        "years": ["2024", "2025"],
        "question": "训练中注意力 logits 会随训练变大、softmax 越来越尖，这会带来什么问题？有哪些缓解手段？",
        "answerMd": r'''**一句话核心**：logits 无界增长会让 softmax 趋向 one-hot——注意力熵塌缩、梯度变小且分布僵化，还可能伴随异常大的激活；常用缓解是温度缩放、对 Q/K 做 Norm（QK-Norm）以及 logit 惩罚。

**1. 为什么 logits 会变大。** 训练目标鼓励模型「更确定地」检索相关信息，Q、K 的尺度可以一路增长；再加上残差流中存在少数维度幅值极大的「massive activation」，部分头的 logits 会很大。后果是 softmax 接近 one-hot：注意一两个 token，其他位置权重近 0，梯度 $\mathrm{diag}(p) - pp^\top$ 缩小，长尾位置学不到东西，泛化与外推都变差。

**2. 缓解手段。** 一是温度：推理时对 logits 除以 $T$，$T>1$ 平滑分布，这就是采样温度的来历；训练中部分工作给注意力 logits 乘小于 1 的系数或直接学温度。二是 QK-Norm：对 Q、K 沿头维度做 RMSNorm 再点积，把 logits 幅度钳在 $\sqrt{d_k}$ 级别，Gemma 2、Qwen 3 等模型采用了这类做法（Qwen 3 同时去掉了 QKV bias）。三是正则：对 router/logit 加 z-loss 类惩罚抑制无界增长；四是从结构上限制，如给注意力加 Sigmoid 门控（gated attention）。

**3. 面试要点。** 能把「熵塌缩—梯度消失—外推变差」这条因果链讲清楚，并指出 QK-Norm 与温度的适用场景（训练稳定性 vs 推理采样控制），再提一句 attention sink 现象（大量注意力堆到首个 token 上，可用可学习的 sink/保留首 token KV 缓解），基本就是满分答案。''',
        "keyPoints": [
            "logits 无界增长导致 softmax 熵塌缩、接近 one-hot",
            "one-hot 化使 softmax 梯度趋零、长尾关系学不到、外推变差",
            "QK-Norm 把 logits 幅度钳住，Qwen3/Gemma2 等已采用",
            "采样温度是推理侧对应物；z-loss/门控是训练侧正则",
            "attention sink：注意力过度集中到个别 token，可用保留 sink 的 KV 缓解",
        ],
        "followUps": [
            {"q": "采样温度调高调低分别发生什么？", "a": "温度小于 1 放大 logits 差异，分布更尖、输出更保守但更重复；大于 1 压平分布，更多样但更容易胡说。温度只改 softmax 形状，不改变排序，top-1 贪心结果不受影响。"},
        ],
    },
    {
        "id": "transformer-006",
        "topic": "Attention机制",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 5,
        "companies": ["字节", "阿里", "腾讯", "百度", "美团"],
        "years": ["2024", "2025"],
        "question": "手写一个 scaled dot-product attention，要求支持 causal mask，并用 numpy 验证正确性。",
        "answerMd": r'''**一句话核心**：三步——logits = QK^T/sqrt(d_k)、mask 处用大负数、softmax 后乘 V；面试时先写对形状，再主动讲数值稳定与 mask 语义。

实现要点：先向面试官确认 Q/K/V 形状与是否 causal；mask 加在 logits 上、softmax 前减最大值保证数值稳定；最后用行和为 1、被 mask 位置权重为 0、未来位置不影响过去这三个性质验证。扩展点：换成 torch 可直接用 F.scaled_dot_product_attention（内部走 FlashAttention）；要支持 batch 与多头时把维度变成 (B, h, n, d_k) 再广播 mask；padding mask 与 causal mask 用逻辑与合并。''',
        "keyPoints": [
            "先算 logits = QK^T / sqrt(d_k)，形状 (n_q, n_k)",
            "mask 用 where 置大负数且在 softmax 之前",
            "softmax 前减行最大值保证数值稳定",
            "验证：行和为 1、mask 位为 0、因果性成立",
        ],
        "followUps": [
            {"q": "怎么把它改成支持 batch 和多头？", "a": "输入变成 (B, h, n, d_k)，矩阵乘最后一维自动广播；mask 变成 (B, 1, n, n) 与 (B, 1, 1, n_k) 两类，逻辑或后广播即可。"},
        ],
        "code": {
            "lang": "python",
            "caption": "numpy 版 scaled dot-product attention + causal mask",
            "content": r'''import numpy as np

def softmax(x, axis=-1):
    x = x - x.max(axis=axis, keepdims=True)      # 数值稳定：减最大值
    e = np.exp(x)
    return e / e.sum(axis=axis, keepdims=True)

def scaled_dot_product_attention(Q, K, V, mask=None):
    # Q: (n_q, d_k)  K, V: (n_k, d_k)
    d_k = Q.shape[-1]
    logits = Q @ K.T / np.sqrt(d_k)               # (n_q, n_k) 缩放防饱和
    if mask is not None:
        logits = np.where(mask, logits, -1e9)     # 不可见位置置大负数
    A = softmax(logits)                           # 每行一个分布
    return A @ V, A                               # (n_q, d_k), (n_q, n_k)

n, d = 6, 16
Q, K, V = np.random.randn(3, n, d)
causal = np.tril(np.ones((n, n), dtype=bool))     # 下三角因果 mask
out, A = scaled_dot_product_attention(Q, K, V, mask=causal)

assert np.allclose(A.sum(-1), 1.0, atol=1e-6)     # 每行和为 1
assert np.allclose(np.where(causal, A, 0.0), A)   # 未来位置权重为 0
print(out.shape, "ok")''',
        },
    },
    {
        "id": "transformer-007",
        "topic": "Attention机制",
        "type": "手撕",
        "difficulty": 4,
        "frequency": 4,
        "companies": ["字节", "阿里", "快手", "华为"],
        "years": ["2024", "2025"],
        "question": "用 PyTorch 手写一个完整的多头自注意力模块（含因果 mask），说说每一步的形状变化。",
        "answerMd": r'''**一句话核心**：QKV 合并一次线性投影、按 (B, h, n, d_k) 切头、缩放点积加因果 mask、softmax 加权后拼回并过输出投影；核心是头维度放在倒数第二维方便批量矩阵乘。

形状主线（B 批量、N 序列长、D 模型宽、h 头数、d_k=D/h）：输入 (B, N, D) → QKV 投影 (B, N, 3D) → 切三份 → view+transpose 得 (B, h, N, d_k) → logits (B, h, N, N) → softmax 后 (B, h, N, N) 乘 V → (B, h, N, d_k) → transpose+reshape 回 (B, N, D) → 输出投影 (B, N, D)。

面试易被追问：为什么 QKV 合成一个 Linear（一次 GEMM 更快）；为什么 reshape 前要 contiguous（transpose 后内存不连续，view 会报错）；dropout 加在哪（softmax 权重上、残差前）；推理时怎么改成带 KV Cache 的增量版本。如果时间充裕，可以顺手把 GQA（KV 头数少于 Q 头数、repeat_interleave 展开）讲一句，加分明显。''',
        "keyPoints": [
            "QKV 合并成一次 3D 宽度的 Linear，切头用 view + transpose",
            "logits 形状 (B, h, N, N)，mask 后 softmax 在最后一维",
            "输出要 contiguous 后再 reshape 回 (B, N, D)",
            "dropout 加在注意力权重与输出投影处",
            "加分项：讲 GQA 改法与 KV Cache 增量推理",
        ],
        "followUps": [
            {"q": "transpose(1,2) 之后为什么还要 contiguous？", "a": "transpose 只是改变 stride 的视图，内存仍按旧顺序排；view/reshape 要求逻辑连续，所以先 .contiguous() 拷贝一份，否则 view 会报错或要用 reshape 触发拷贝。"},
        ],
        "code": {
            "lang": "python",
            "caption": "多头自注意力（MHA）最小实现",
            "content": r'''import torch
import torch.nn as nn
import torch.nn.functional as F

class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, n_heads, dropout=0.0):
        super().__init__()
        assert d_model % n_heads == 0
        self.h, self.d_k = n_heads, d_model // n_heads
        self.qkv = nn.Linear(d_model, 3 * d_model)   # QKV 合并投影
        self.proj = nn.Linear(d_model, d_model)      # 输出投影 W_O
        self.drop = nn.Dropout(dropout)

    def forward(self, x, causal=True):
        B, N, D = x.shape
        q, k, v = self.qkv(x).chunk(3, dim=-1)       # 各 (B, N, D)
        # 切头: (B, h, N, d_k)
        q, k, v = (t.view(B, N, self.h, self.d_k).transpose(1, 2)
                   for t in (q, k, v))
        logits = q @ k.transpose(-2, -1) / self.d_k ** 0.5   # (B, h, N, N)
        if causal:
            m = torch.triu(torch.ones(N, N, dtype=torch.bool,
                                      device=x.device), 1)
            logits = logits.masked_fill(m, float("-inf"))
        A = self.drop(F.softmax(logits, dim=-1))
        out = (A @ v).transpose(1, 2).contiguous().view(B, N, D)
        return self.proj(out)

layer = MultiHeadAttention(64, 8)
x = torch.randn(2, 10, 64)
print(layer(x).shape)            # torch.Size([2, 10, 64])''',
        },
    },
    # ---------------------------------------------------------------- 注意力变体
    {
        "id": "transformer-008",
        "topic": "注意力变体",
        "type": "八股",
        "difficulty": 3,
        "frequency": 5,
        "companies": ["字节", "阿里", "DeepSeek", "月之暗面"],
        "years": ["2024", "2025"],
        "question": "MHA、MQA、GQA 三种注意力有什么区别？GQA 是怎么分组的，训练和推理分别要注意什么？",
        "answerMd": r'''**一句话核心**：MHA 每个查询头一套 KV；MQA 所有查询头共享一套 KV（显存最省但掉点）；GQA 折中——查询头分组共享 KV 组，是 Llama 2/3、Qwen 等主流开源模型的默认选择。

**1. 动机：KV Cache 是解码瓶颈。** 解码每步都要读全部历史 KV，显存占用与带宽都与 KV 头数成正比。MQA（2019）把 KV 头压到 1 个：cache 缩小 $h$ 倍，但只保留一个 KV 子空间，质量下降明显。GQA 把 $h_q$ 个查询头分成 $g$ 组，每组共享一个 KV 头：$g=1$ 退化为 MQA，$g=h_q$ 就是 MHA，显存节省 $h_q/g$ 倍。

**2. 分组方式。** 常见是相邻查询头共用一组 KV（如 32 个查询头、8 个 KV 头，每 4 个查询头绑一组）；实现上把 KV 沿头维 repeat_interleave 或 expand 到查询头数再算标准注意力。KV 头数一般取 8，且要能整除 TP 并行度。

**3. 训练与推理注意点。** 直接从零用 GQA 训练即可；论文还给出 uptraining 方案——把训好的 MHA 检查点按组做 mean-pooling 转成 GQA，再用约 5% 的原训练量继续训就能恢复大部分质量，这是迁移已有模型常用的一步。推理侧收益直接体现在 KV Cache 显存与 decode 带宽上：以 Llama 3 8B（32 查询头/8 KV 头）为例，KV Cache 是 MHA 的四分之一。''',
        "keyPoints": [
            "MQA 全头共享 1 组 KV，省显存但掉点；MHA 每头独立",
            "GQA 折中：g 组 KV，g=1 退化 MQA、g=h 退化 MHA",
            "实现：KV 头 repeat_interleave 到查询头数",
            "MHA 检查点可按组 mean-pool 转 GQA 后用少量算力 uptrain",
            "KV Cache 与 decode 带宽随 KV 头数线性下降",
        ],
        "followUps": [
            {"q": "GQA 分组该按什么顺序共享？", "a": "论文用相邻头分组（如每连续 4 个查询头一组）效果与随机分组相当；转换已有 MHA 模型时按头在训练中学到的功能就近合并更自然，实践中 mean-pool 相邻头即可。"},
        ],
    },
    {
        "id": "transformer-009",
        "topic": "注意力变体",
        "type": "八股",
        "difficulty": 4,
        "frequency": 4,
        "companies": ["DeepSeek", "字节", "月之暗面", "阿里"],
        "years": ["2024", "2025", "2026"],
        "question": "DeepSeek 的 MLA（多头潜在注意力）是怎么把 KV Cache 压下来的？为什么它还要配一个解耦的 RoPE？",
        "answerMd": r'''**一句话核心**：MLA 把每个 token 的 K、V 联合低秩压缩成一个共享的 latent 向量并只缓存它，注意力时再展开成多头；RoPE 的位置旋转与矩阵吸收不兼容，所以额外缓存一小段带 RoPE 的解耦 key。

**1. 低秩压缩。** 标准 MHA 每个 token 每层要存全部头的 K 和 V。MLA 把它们一起投到低维 latent $c_{KV} = W_{DKV} x$（维度远小于总 KV 维度），只缓存 $c_{KV}$；需要时用上投影 $W_{UK}, W_{UV}$ 还原各头的 $k, v$。由于压缩是跨头联合的，容量利用率比 GQA「共享」更高，质量基本不掉。缓存量从 $O(h \cdot d_k)$ 降到 $O(d_{latent})$，常能压到 GQA 的几分之一甚至更低。

**2. 矩阵吸收。** 点积 $q^\top (W_{UK} c_{KV})$ 可以把 $W_{UK}$ 吸进查询侧：$(W_{UK}^\top q)^\top c_{KV}$，于是推理时根本不必真的还原 K，直接拿 latent 参与打分，进一步省计算；V 侧同理吸收进输出投影。

**3. 为什么要解耦 RoPE。** RoPE 是对每个头的 K 按位置做旋转，旋转矩阵依赖 (m-n)，破坏了「$W_{UK}$ 可以挪到 q 侧」的吸收性质——q 与 k 的旋转无法合并成只依赖相对位置的因子。解法是解耦 RoPE：额外保留一个极小的每头 rope key（和 q 侧对应部分）做位置旋转，与不带位置信息的内容通路各自打分再相加；因此 MLA 实际缓存的是 latent 向量加一小段 rope key。

**4. 取舍。** MLA 的代价是训练/推理多几次小投影、prefill 实现更复杂；收益是长上下文下 KV 显存与带宽大幅下降。它是 DeepSeek V2/V3/R1 系列的标配，2025 年起多家模型跟进类似思路。''',
        "keyPoints": [
            "KV 联合低秩压缩成共享 latent，只缓存 latent 向量",
            "上投影可被吸收进 Q 与输出投影，推理无需显式还原 K/V",
            "RoPE 旋转与吸收不兼容，故用小维度解耦 rope key 单独缓存",
            "缓存压缩比 GQA 更高且质量损失小，代价是投影与实现复杂度",
        ],
        "followUps": [
            {"q": "MLA 和 GQA 怎么选？", "a": "重推理吞吐、长上下文场景选 MLA，缓存与带宽优势大；追求实现简单、生态兼容（多数推理框架对 GQA 支持最成熟）选 GQA。MLA 的算子要专门优化，否则吸收矩阵的额外计算可能吃掉收益。"},
        ],
    },
    {
        "id": "transformer-010",
        "topic": "注意力变体",
        "type": "八股",
        "difficulty": 4,
        "frequency": 5,
        "companies": ["字节", "阿里", "NVIDIA", "华为"],
        "years": ["2023", "2024", "2025"],
        "question": "FlashAttention 快在哪？它改变了计算量吗？讲讲 online softmax 的思想和 FA2/FA3 的改进。",
        "answerMd": r'''**一句话核心**：FlashAttention 是精确注意力的 IO 优化——通过分块 tiling 与 online softmax，把注意力从「在 HBM 里物化 $n \times n$ 矩阵、来回读写三次」变成「在 SRAM 里分块算完即丢」，FLOPs 不变但访存量大幅下降。

**1. 瓶颈在 IO 不在 FLOPs。** 朴素实现要把 $n \times n$ 的 logits、softmax 结果写回 HBM 再读回来乘 V，注意力是 memory-bound 的。GPU 的 SRAM 比 HBM 快一个量级，于是把 Q/K/V 切成块放进 SRAM，一块一块算出最终输出，$n \times n$ 矩阵从不落盘。IO 复杂度从 $O(n^2 + nd)$ 降到约 $O(n^2 d^2 / M)$（$M$ 是 SRAM 大小），长序列下收益巨大。

**2. online softmax。** softmax 需要先知道全行最大值和分母，而分块时只看到局部数据。解法是维护运行统计量：全局最大值 $m$、指数和 $l$ 与部分输出 $o$，每来一个新块就更新 $m \leftarrow \max(m, m_{blk})$，旧的 $l, o$ 乘修正因子 $\exp(m_{old} - m_{new})$ 再累加新块，最后统一归一化。数学上与标准 softmax 完全等价，这就是「在线」的含义。

**3. 反向与 FA2/FA3。** 反向不存 $n \times n$ 矩阵，只存输出 $O$ 和随机状态，重算前向得到所需中间量，用空间换显存。FA2 调整循环结构与并行方式、把 softmax 相关的非矩阵乘 FLOPs 减半，并沿序列维度并行以提高占用率；FA3 面向 Hopper 用异步指令与流水线进一步隐藏访存，官方报告相对 FA2 有约 1.5~2 倍提升。如今主流训练框架的注意力后端基本都是 FlashAttention 系。''',
        "keyPoints": [
            "精确算法、不近似；省的是 HBM 访存而不是 FLOPs",
            "分块 tiling + online softmax，n x n 矩阵从不物化",
            "online softmax 用 (m, l, o) 运行量与新块修正因子等价合并",
            "反向靠重算省显存；FA2 减非 matmul 开销并改并行，FA3 吃 Hopper 异步",
        ],
        "followUps": [
            {"q": "为什么 FlashAttention 对训练收益比推理更明显？", "a": "训练要算整个 n x n 注意力并保存/重算，prefill 一次算长序列时平方项大；而短序列 decode 每步只有 1 个 query，注意力矩阵只有 1 行，瓶颈在 KV 读取而非 logits 计算，所以 decode 更多靠 GQA/MLA、分页 KV 与 batching 提速。"},
        ],
    },
    {
        "id": "transformer-011",
        "topic": "注意力变体",
        "type": "手撕",
        "difficulty": 4,
        "frequency": 3,
        "companies": ["字节", "NVIDIA", "华为"],
        "years": ["2024", "2025"],
        "question": "手写 online softmax，并写一个 toy 版的 flash 分块注意力，解释每一步在修什么。",
        "answerMd": r'''**一句话核心**：online softmax 用运行最大值 m 与指数和 l 在单遍扫描中维护分布统计量；flash 版进一步把输出 o 也在线缩放累加，做到不物化 n x n 矩阵。

关键点有三个：一是新块到来时先更新全局最大值 $m$，旧的 $l$ 与 $o$ 都要乘修正因子 $\exp(m_{old} - m_{new})$，因为它们是按旧最大值归一化的；二是当前块的概率 $p$ 用新最大值算；三是全部块处理完后才用 $l$ 做一次归一化，而不是每块各归一化一次。面试时先写一维 online softmax 打底，再写块状累加版，边写边说「这等价于标准 softmax，只是把全局 max/sum 改成增量维护」。''',
        "keyPoints": [
            "维护运行量 (m, l)：m 是全局最大，l 是缩放后的指数和",
            "新块更新 m 后，旧统计量乘 exp(m_old - m_new) 修正",
            "输出 o 同步在线累加，最后统一除 l 归一化",
            "全程不需要完整一行的 logits，内存 O(block)",
        ],
        "followUps": [
            {"q": "online softmax 结果和普通 softmax 完全一致吗？", "a": "数学上恒等，浮点上可能有极小的舍入差异，因为减的最大值路径不同；两者都是先减最大值再指数，误差量级在 1e-7 左右，可以 allclose 验证。"},
        ],
        "code": {
            "lang": "python",
            "caption": "online softmax 与 toy 版分块注意力",
            "content": r'''import numpy as np

def online_softmax(x):
    """单遍扫描 online softmax：只维护 (m, l)"""
    m, l = -np.inf, 0.0
    for xi in x:
        m_new = max(m, xi)
        l = l * np.exp(m - m_new) + np.exp(xi - m_new)   # 旧和按比例修正
        m = m_new
    return np.exp(x - m) / l                             # 末尾统一归一化

def flash_toy(q, K, V, block=64):
    """分块累积：从不物化完整 logits 矩阵"""
    d_k = q.shape[-1]
    m, l = -np.inf, 0.0
    o = np.zeros(V.shape[1])
    for s in range(0, len(K), block):
        logits = K[s:s+block] @ q / np.sqrt(d_k)   # 当前块 logits
        m_new = max(m, logits.max())
        p = np.exp(logits - m_new)                 # 当前块概率
        corr = np.exp(m - m_new)                   # 旧结果的修正因子
        l = l * corr + p.sum()
        o = o * corr + p @ V[s:s+block]            # 输出同步缩放累加
        m = m_new
    return o / l

x = np.random.randn(1000)
assert np.allclose(online_softmax(x), np.exp(x - x.max()) / np.exp(x - x.max()).sum())
q, K, V = np.random.randn(3, 256, 32)
ref = np.exp(K @ q / np.sqrt(32) - (K @ q / np.sqrt(32)).max())
assert np.allclose(flash_toy(q, K, V), (ref / ref.sum()) @ V, atol=1e-5)
print("ok")''',
        },
    },
    {
        "id": "transformer-012",
        "topic": "注意力变体",
        "type": "八股",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["阿里", "Google", "面壁智能"],
        "years": ["2024", "2025"],
        "question": "滑窗注意力（Sliding Window Attention）为什么能省算力？叠加多层之后模型能看到多远？",
        "answerMd": r'''**一句话核心**：SWA 让每个位置只对前后 $w$ 个 token 做注意力，把每层的成本从 $O(n^2)$ 降到 $O(n \cdot w)$、KV Cache 从 $O(n)$ 降到 $O(w)$；多层堆叠后感受野逐层扩大，$L$ 层约能看到 $L \times (w-1) + 1$ 范围。

**1. 为什么可行。** 语言建模的大多数注意力集中在局部：相邻 token、短语和句内依赖占大头，全局长程依赖只占少数。SWA 把「每层全局」换成「每层局部、跨层间接全局」：第 1 层看到距离 $w$，第 2 层经一次聚合看到 $2w$，$L$ 层后信息可以传递 $L(w-1)+1$ 远。Mistral 早期模型（窗口 4096）和 Gemma 系列（局部/全局层交错）都用了这个思想。

**2. 实现要点。** KV Cache 只需保留窗口内的 KV（环形缓冲覆盖写），decode 时显存与带宽都是常数级；训练时用带状 mask，FlashAttention 有对应内核（banded/local attention）。只做 SWA 的模型对「精确复述很远的开头」会变弱，所以工程上流行混合：每隔若干层放一个全局注意力层（如 Gemma 3 大约 5 个局部层配 1 个全局层），局部层管效率、全局层管长程检索，KV 也可只对全局层做完整缓存。

**3. 追问预备。** 若被问「窗口外的信息是怎么传过去的」，答：逐层聚合——远处信息先被中间 token 汇总，再经后续层的局部注意力一步步传过来，类似 CNN 感受野扩张；这也是为什么混合架构的全局层比例不需要太高。''',
        "keyPoints": [
            "每层成本 O(n*w)、KV Cache 常数级（环形缓冲）",
            "L 层堆叠后有效感受野约 L*(w-1)+1",
            "纯局部对远程精确检索弱，常与全局层交错（如 5:1）",
            "FlashAttention 有 banded/local 内核支撑训练效率",
        ],
        "followUps": [
            {"q": "SWA 模型做长文档问答时最可能暴露什么短板？", "a": "需要精确定位文档开头细节的检索类问题（needle in a haystack 中放在窗口外的信息），因为信息要经过多层压缩传递，容易失真；所以长上下文评测要专门测远程检索，而不只看困惑度。"},
        ],
    },
    {
        "id": "transformer-013",
        "topic": "注意力变体",
        "type": "八股",
        "difficulty": 4,
        "frequency": 3,
        "companies": ["字节", "华为", "智谱"],
        "years": ["2024", "2025"],
        "question": "线性注意力是怎么把复杂度降到 O(n) 的？代价是什么？",
        "answerMd": r'''**一句话核心**：把 softmax 核换成可分离的特征映射 $\phi$，利用结合律先算 $\phi(K)^\top V$ 得到 $O(d_k \times d_v)$ 的「状态矩阵」，再与 $\phi(Q)$ 相乘，复杂度降为 $O(n d^2)$；代价是丢掉 softmax 的精确检索能力与归一化的表达力。

**1. 推导。** 注意力可写成 $\mathrm{softmax}(QK^\top)V \approx D^{-1}\,(\phi(Q)(\phi(K)^\top V))$，其中 $D^{-1}$ 是归一化分母 $\phi(Q)(\phi(K)^\top \mathbf{1})$。关键在结合顺序：先算 $K$ 侧的 $\phi(K)^\top V$（一个 $d_k \times d_v$ 矩阵，与序列长度无关），再对每个 query 只做一次矩阵乘，整层 $O(n d_k d_v)$ 而非 $O(n^2 d)$。它还有天然的递推形式：状态 $S_t = S_{t-1} + \phi(k_t) v_t^\top$，解码时每步 $O(1)$ 更新、状态恒定大小。

**2. 代价。** 一是 softmax 的「尖锐检索」没了：softmax 注意力相当于把对的 key 精确挑出来，而线性核是光滑求和，做精确召回（复制、长程查找）任务明显变差；二是状态是有界的，信息不断被覆盖，相当于固定大小的记忆；三是归一化分母数值不稳定（Performer 用随机特征缓解）。因此线性注意力的质量普遍低于全注意力，单独做主干不够强。

**3. 2024 年后的演进。** RetNet 给状态加衰减、DeltaNet 用 delta rule（按误差改写旧状态）增强记忆更新、门控版本（Gated DeltaNet）进一步提升；实践中它们更多以「混合层」身份出现：大部分层用线性注意力省算力，少量层保留全注意力做精确检索。''',
        "keyPoints": [
            "核化后利用结合律先算 phi(K)^T V，复杂度 O(n d^2)",
            "等价的递推形式：状态矩阵 S_t = S_{t-1} + phi(k_t) v_t^T，decode O(1)/步",
            "softmax 的精确检索与尖锐分布丢失，召回类任务变差",
            "状态有界 = 固定大小记忆，会被覆盖",
            "现代用法是混合层：线性注意力为主 + 少量全注意力",
        ],
        "followUps": [
            {"q": "Performer 是怎么近似 softmax 核的？", "a": "用正交随机特征（FAVOR+）构造 phi，使 phi(q)^T phi(k) 无偏估计 exp(q·k)；对正负 logit 分别配随机特征保证非负。它证明了 softmax 可被线性化，但估计方差与所需特征数限制了实际效果。"},
        ],
    },
    {
        "id": "transformer-014",
        "topic": "注意力变体",
        "type": "八股",
        "difficulty": 4,
        "frequency": 3,
        "companies": ["字节", "华为", "MiniMax"],
        "years": ["2024", "2025"],
        "question": "对比一下 Mamba/SSM 和 Transformer：状态空间模型强在哪，弱在哪，现在为什么流行做混合架构？",
        "answerMd": r'''**一句话核心**：SSM 用线性递推 $h_t = \bar A h_{t-1} + \bar B x_t,\ y_t = C h_t$ 处理序列，推理状态恒定、上下文线性扩展；但固定大小的状态削弱精确召回，所以 2024 年后的主流是「SSM/线性层为主 + 少量全注意力」的混合架构。

**1. 机制对比。** Transformer 每层把全部历史 KV 存下来，注意力是内容寻址的精确查找，推理每步成本随上下文线性增长；SSM 把历史压缩进固定维度的隐状态，训练可用并行 scan，推理每步 $O(1)$ 更新、显存常数。Mamba 的关键创新是「选择性」：让 $\bar B, \bar C, \Delta$ 依赖输入，使状态能按内容决定记什么忘什么，突破了传统 SSM 时不变的局限。

**2. 强弱项。** 强项：长序列吞吐、decode 延迟稳定、上下文扩展成本低。弱项：状态有界导致精确复制/检索弱（如从 100 万 token 前文原样抄一段），多步关联记忆不如注意力；训练生态与算子成熟度也差一些。Mamba-2 的 SSD 视角进一步把它和线性注意力统一：SSM 可视为带衰减的线性注意力。

**3. 混合架构为什么赢。** 局部与检索用 SSM 层省钱，每隔几层插一个全注意力层负责精确记忆，两边取长：Jamba、Zamba 走 Mamba+注意力，MiniMax 的 lightning attention 混合、Qwen3-Next 的 Gated DeltaNet 与门控注意力 3:1 交错、Kimi Linear 的 KDA 与 MLA 混合，基本都遵循「大部分层线性、每 4~8 层一次全注意力」的配方，实验显示混合比例不需要很高就能保住检索能力。''',
        "keyPoints": [
            "SSM 递推状态固定大小，训练并行 scan、推理 O(1)/步",
            "Mamba 选择性机制：B、C、Delta 随输入变化，可按内容取舍记忆",
            "弱在精确召回与有界记忆，算子生态不如注意力成熟",
            "Mamba-2 SSD 将 SSM 与带衰减的线性注意力统一",
            "混合层（如 3:1~7:1）成为 2025~2026 主流配方",
        ],
        "followUps": [
            {"q": "SSM 的推理显存为什么不随上下文增长？", "a": "它不存历史 KV，而是把历史持续压缩进固定形状的隐状态矩阵 h，每步用新 token 更新一次；代价是旧细节被覆盖，等价于有损压缩的记忆。"},
        ],
    },
    {
        "id": "transformer-015",
        "topic": "注意力变体",
        "type": "八股",
        "difficulty": 4,
        "frequency": 3,
        "companies": ["DeepSeek", "月之暗面", "字节"],
        "years": ["2025", "2026"],
        "question": "2025 年以来稀疏注意力这条线上有哪些代表性工作？它们共同的思路是什么？",
        "answerMd": r'''**一句话核心**：共同思路是「不是每个 query 都需要扫全部 key」——按块把 key 分成局部窗、压缩摘要与少量被选中的重要块，只对这几类做注意力，把超长上下文的计算和 KV 访存都降下来，同时尽量保持可训练、硬件友好。

**1. 代表工作。** DeepSeek 的 NSA（原生稀疏注意力，2025 初）：每个 query 对三类分支打分——滑窗（邻近细节）、块级压缩（把连续 key 压成摘要 token）、top-n 块选择（挑出少数重要块），三路分数门控融合，且设计成能用 GEMM 硬件高效执行、端到端训练。月之暗面的 MoBA（2025 初）：把上下文切块，每个 query 用一个门控在「全选」与「top-k 块」之间路由，作为 Mixture of Block Attention 融进现有框架。DeepSeek V3.2 实验版（2025 下半年）引入稀疏注意力（DSA）：用一个轻量索引器给每个 query 挑选少量关键 token 参与精确注意力，主打长上下文推理成本大幅下降。各家模型（如 MiniMax、Qwen 系的混合层）也在把局部/全局/稀疏组合起来用。

**2. 为什么现在流行。** 上下文到 128K~1M 后，全注意力的 $n^2$ 计算与 KV 带宽都成了硬瓶颈，而注意力分布高度稀疏且可预测；MoE 证明「稀疏激活」在 FFN 上成立，同样的逻辑搬到注意力上。

**3. 风险点。** 块选择是离散决策，训练不稳定或选择偏差会造成能力退化；需要精心设计保证「检索密集型任务」（大海捞针、多跳问答）不掉点，这也是各家论文重点报告的内容。''',
        "keyPoints": [
            "核心假设：每个 query 只依赖少量关键 key，注意力可按块稀疏化",
            "NSA：滑窗 + 压缩摘要 + top-n 块选择三路分支，硬件对齐可训练",
            "MoBA：块级 mixture，门控在全局与 top-k 块间路由",
            "DSA（V3.2）：轻量索引器选 token + 精确注意力，降长上下文成本",
            "风险：离散选择训练不稳、检索密集任务可能掉点",
        ],
        "followUps": [
            {"q": "稀疏注意力和滑窗、线性注意力是什么关系？", "a": "滑窗是固定模式的稀疏（只看局部）；线性注意力把全历史压进固定状态，等价于无限窗的有损压缩；稀疏注意力是内容自适应的稀疏——动态挑重要块，兼顾精度与成本，介于两者之间。"},
        ],
    },
    # ---------------------------------------------------------------- 位置编码
    {
        "id": "transformer-016",
        "topic": "位置编码",
        "type": "八股",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["字节", "百度", "腾讯"],
        "years": ["2023", "2024"],
        "question": "正弦位置编码是怎么设计的？它能表示相对位置吗，为什么后来大多换成了别的方案？",
        "answerMd": r'''**一句话核心**：正弦编码用一组几何递减频率的 $\sin/\cos$ 给每个位置生成唯一向量，任意固定偏移的编码可由低一维的线性变换表示（有相对性），但它是外加的绝对信号且外推有限，逐步被 RoPE 等相对位置方案替代。

**1. 设计。** $PE_{(pos, 2i)} = \sin(pos/10000^{2i/d})$，$PE_{(pos, 2i+1)} = \cos(pos/10000^{2i/d})$。不同维度对应不同频率：低维高频（区分相邻位置），高维低频（区分远距离位置），类似二进制/时钟的多分辨率刻度，每个位置得到一个独特且光滑变化的向量。

**2. 相对性质。** 对任意偏移 $k$，$PE_{pos+k}$ 可以写成 $PE_{pos}$ 的线性变换（二维平面上的旋转，矩阵只依赖 $k$），所以模型原则上能学到相对关系。但注意：注意力打分本身用绝对位置相加，$\langle q+PE_m, k+PE_n\rangle$ 里既有相对项也有绝对项与交叉项，相对性并不干净。

**3. 为什么被替代。** 一是外推：训练长度外的位置模式没见过，直接外推质量骤降；二是与注意力机制分离——位置信息加在输入上，深层网络可能「稀释」它，而 RoPE 直接在每次注意力打分时注入相对信息；三是可学习绝对编码（GPT-2 式）在训练长度内与正弦效果相当但没有外推优势。于是 Llama 系等用 RoPE，BLOOM 用 ALiBi，正弦编码主要留在早期模型和部分视觉 Transformer 里。''',
        "keyPoints": [
            "多频率 sin/cos，几何递减频率形成多分辨率位置刻度",
            "固定偏移 k 的编码可由只依赖 k 的线性变换（旋转）得到",
            "与注意力相加的方式让相对性不纯粹，深层易被稀释",
            "外推差是硬伤，被 RoPE/ALiBi 等相对方案取代",
        ],
        "followUps": [
            {"q": "可学习绝对位置编码比正弦差在哪？", "a": "训练最大长度之外没有定义，无法外推；参数多一份。但训练长度内两者效果接近，GPT-2 用可学习编码也没有明显劣势，说明瓶颈主要在外推而非表达。"},
        ],
    },
    {
        "id": "transformer-017",
        "topic": "位置编码",
        "type": "八股",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["字节", "阿里", "智谱"],
        "years": ["2023", "2024", "2025"],
        "question": "把绝对位置编码和相对位置编码这条演进线梳理一遍：各代表方案怎么做，核心取舍是什么？",
        "answerMd": r'''**一句话核心**：演进主线是「从外加的绝对信号，走向直接作用在注意力打分里的相对信号」——正弦/可学习 → T5 相对 bias → RoPE（旋转相对）→ ALiBi（线性距离惩罚），核心取舍在外推能力、表达力与实现复杂度。

**1. 绝对位置。** 正弦或可学习矩阵加在输入 embedding 上：简单、直观，但长度受训练限制、相对关系不纯粹。可学习版本多一组参数且不可外推。

**2. 加性相对 bias（T5/Shaw）。** 在注意力 logits 上加一个只依赖 $(i-j)$ 的可学习偏置（T5 用分桶 + 跨头共享的标量 bias）：相对关系直接进入打分，长度理论上可延展；缺点是每个距离要学参数，超长距离分桶粗糙，且与 KV Cache 配合要多传相对距离信息。

**3. RoPE。** 把位置做成 Q/K 上的二维旋转，$\langle R_m q, R_n k\rangle = \langle q, R_{n-m} k\rangle$，天然只依赖相对距离、无参数、支持 KV Cache 增量旋转，成为 Llama/Qwen/DeepSeek 等的标配；长上下文扩展也围绕它展开（插值/调 base）。

**4. ALiBi。** 不加位置向量，直接给 logits 减 $m_h \cdot |i-j|$ 的线性惩罚，每头用几何递减斜率：实现极简、外推效果好，BLOOM/MPT 采用；但对「远距离也重要」的任务有系统性偏置，且位置感知不如 RoPE 细腻。

**5. 取舍总结。** RoPE：质量与外推/扩展性平衡最好，生态最大；ALiBi：免训练外推最简单；T5 bias：表达力强但参数与实现成本高；绝对编码：如今主要出现在小模型或多模态场景。''',
        "keyPoints": [
            "绝对：正弦/可学习加在输入上，外推差",
            "T5 相对 bias：logits 加只依赖距离的偏置，表达强、成本高",
            "RoPE：Q/K 旋转，天然相对、免参数、KV Cache 友好",
            "ALiBi：logits 减线性距离惩罚，免参数外推好但偏局部",
            "主流 LLM 基本收敛到 RoPE（配合扩展技术）",
        ],
        "followUps": [
            {"q": "NoPE（不加位置编码）为什么也能工作？", "a": "decoder 的因果 mask 本身就破坏了置换对称性：每个位置能看见的前缀集合不同，注意力可以从中推断位置。实验显示小模型用 NoPE 也能学到隐式位置感知，但显式 RoPE 仍是更稳的选择。"},
        ],
    },
    {
        "id": "transformer-018",
        "topic": "位置编码",
        "type": "八股",
        "difficulty": 4,
        "frequency": 5,
        "companies": ["字节", "阿里", "DeepSeek", "月之暗面"],
        "years": ["2023", "2024", "2025"],
        "question": "推导一下 RoPE：它是怎么做到「内积只依赖相对位置」的？有哪些好性质？",
        "answerMd": r'''**一句话核心**：RoPE 把每个位置的 q、k 按位置相关的角度做二维块旋转，旋转矩阵作用在两侧后，内积等于「先按相对角度 $m-n$ 旋转」，因此打分天然只依赖距离；它免参数、外推可扩展、与 KV Cache 兼容。

**1. 推导。** 目标：找函数 $f(x, m)$，使 $\langle f(q, m), f(k, n)\rangle$ 只含 $m - n$。把 $d$ 维向量按相邻两维分成 $d/2$ 个二维子空间，视作复数 $q_t = x_{2t} + i x_{2t+1}$，定义 $f(x, m)_t = x_t e^{i m \theta_t}$，其中 $\theta_t = 10000^{-2t/d}$ 是第 $t$ 个子空间的频率。则 $\langle f(q,m), f(k,n)\rangle = \mathrm{Re}\sum_t q_t k_t^* e^{i(m-n)\theta_t}$，只依赖 $m-n$。写成实数形式就是每两个维度做旋转矩阵 $R_{m\theta_t}$。

**2. 性质。** 一，相对性：内积是关于 $(m-n)$ 的函数，远处角度相位差大、近处小；二，多频率：$\theta_t$ 从 1 到 $1/10000$ 几何分布，低维子空间高频振荡编码近距差异，高维低频编码长程结构，且高频子空间内积随距离震荡衰减、整体呈远程衰减趋势，符合语言局部性；三，无参数、即插即用；四，实现上只需预计算 $\cos(m\theta), \sin(m\theta)$ 表，decode 时对新 token 的 q/k 用当前步的角度旋转即可，与 KV Cache 完美兼容。

**3. 工程细节。** 常与 RMSNorm 配合（先 norm 后旋转）；不同模型旋转的维度配对不同（相邻 vs 半分），加载权重时要注意；长上下文扩展就是围绕 $\theta$ 或 $m$ 的缩放做文章。''',
        "keyPoints": [
            "复数视角：f(x, m)_t = x_t * e^{i m theta_t}",
            "内积化为只依赖 (m-n) 的实部求和，相对性成立",
            "多频率几何分布：近距高频、长程低频，带远程衰减",
            "无参数、预计算 cos/sin 表、与 KV Cache 增量旋转兼容",
            "长上下文扩展（PI/NTK/YaRN）都是对 RoPE 的改造",
        ],
        "followUps": [
            {"q": "RoPE 是绝对位置编码还是相对位置编码？", "a": "实现上是「绝对」的——按绝对位置 m 旋转，但效果是「相对」的——内积只依赖距离。所以常说它是绝对位置编码实现相对位置语义的方案。"},
        ],
    },
    {
        "id": "transformer-019",
        "topic": "位置编码",
        "type": "手撕",
        "difficulty": 4,
        "frequency": 4,
        "companies": ["字节", "阿里", "快手"],
        "years": ["2024", "2025"],
        "question": "手写 RoPE：预计算 cos/sin 表，并实现 q/k 的旋转（要支持 decode 时的位置偏移）。",
        "answerMd": r'''**一句话核心**：预计算每个位置与每个频率对的角度 cos/sin，把 q/k 的相邻两维当平面坐标旋转；decode 时按当前步的 offset 取对应行即可。

实现要点：inv_freq = base^(-2i/d) 生成频率；外积得到 (seq, d/2) 角度表；apply 时把 x[..., 0::2] 与 x[..., 1::2] 配对旋转（注意模型实现有「相邻配对」与「前后半配对」两种，加载权重时要对齐）；decode 时传入 pos_offset = 当前已生成 token 数，只旋转新的一个位置。常见追问：为什么旋转不影响 norm（正交矩阵保内积长度）；为什么直接缓存旋转后的 K 而不是旋转前的（旋转后的 k 与任何未来 q 的相对角度已确定，缓存旋转后最简单，但 prefill/长上下文扩展时也可缓存未旋转形式）。''',
        "keyPoints": [
            "inv_freq = base^(-2i/d)，外积得到位置-频率角度表",
            "偶奇相邻维配对做二维旋转，保持向量范数不变",
            "decode 用 pos_offset 取对应行，天然支持 KV Cache",
            "注意相邻配对与半分配对两种实现约定的差异",
        ],
        "followUps": [
            {"q": "RoPE 的 base 调大有什么效果？", "a": "base 越大低频子空间频率越低、波长越长，同距离的角度差更小、远程衰减更平缓，适合长上下文；代价是近距离位置区分度略降。常见做法是把 base 从 1e4 调到 1e5~1e6 量级配合长上下文训练。"},
        ],
        "code": {
            "lang": "python",
            "caption": "RoPE 预计算与旋转（支持 decode 偏移）",
            "content": r'''import torch

def rope_cache(seq_len, head_dim, base=10000.0):
    assert head_dim % 2 == 0
    inv_freq = 1.0 / (base ** (torch.arange(0, head_dim, 2).float() / head_dim))
    t = torch.arange(seq_len).float()
    freqs = torch.outer(t, inv_freq)          # (seq, d/2) 角度 m*theta
    return freqs.cos(), freqs.sin()           # (seq, d/2)

def apply_rope(x, cos, sin, pos_offset=0):
    # x: (B, N, H, d) 相邻两维一组旋转
    n = x.shape[1]
    cos = cos[pos_offset:pos_offset + n][None, :, None, :]
    sin = sin[pos_offset:pos_offset + n][None, :, None, :]
    x1, x2 = x[..., 0::2], x[..., 1::2]
    out = torch.empty_like(x)
    out[..., 0::2] = x1 * cos - x2 * sin      # 旋转后的实部
    out[..., 1::2] = x1 * sin + x2 * cos      # 旋转后的虚部
    return out

d, B, H = 64, 2, 8
cos, sin = rope_cache(512, d)
q = torch.randn(B, 16, H, d)
k = torch.randn(B, 16, H, d)
qr, kr = apply_rope(q, cos, sin), apply_rope(k, cos, sin)
# 相对性验证：位置 m 的 q 与位置 n 的 k 的打分只随 m-n 变化
assert torch.allclose(qr.norm(dim=-1), q.norm(dim=-1), atol=1e-5)  # 保范数
print("rope ok")''',
        },
    },
    {
        "id": "transformer-020",
        "topic": "位置编码",
        "type": "八股",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["百度", "面壁智能", "零一万物"],
        "years": ["2023", "2024"],
        "question": "ALiBi 是怎么注入位置信息的？它为什么外推好，又有什么局限？",
        "answerMd": r'''**一句话核心**：ALiBi 不加任何位置向量，直接在注意力 logits 上减去与距离成正比的静态惩罚 $m_h \cdot |i-j|$，每个头用不同斜率 $m_h$；它免参数、实现一行、外推平滑，但强加「越远越不重要」的先验。

**1. 做法。** $\mathrm{score}_{ij} = q_i k_j / \sqrt{d_k} - m_h (i - j)$（因果语言建模中只用左向距离）。斜率按几何序列分配给不同头，8 个头取 $\{1/2, 1/4, \dots, 1/256\}$：斜率大的头强局部、斜率小的头弱局部，等效于多尺度位置感受。BLOOM、MPT 用了它。

**2. 为什么外推好。** 训练时模型见到的就是「随距离线性衰减」的规则，推理时序列变长只是衰减线延长，分布外没有新的位置模式需要适应，所以训练 1K 外推到几 K 质量下降平缓；对比可学习/正弦绝对编码，外推时会出现训练没见过的位置值。

**3. 局限。** 一，先验与数据冲突：文档检索、代码跨文件引用等任务需要远距离强依赖，ALiBi 的线性衰减会系统性压低远程注意力，长程检索能力弱于 RoPE 系；二，位置分辨是单调标量，不如 RoPE 的多频率旋转细腻；三，与 KV Cache 兼容但难以做「插值式」长上下文扩展（没有可调的频率参数）。这也是它没有成为 LLM 主流而 RoPE 胜出的主要原因。''',
        "keyPoints": [
            "logits 减 m_h * 距离 的静态惩罚，无参数无向量",
            "斜率按几何序列跨头分配，形成多尺度局部性",
            "外推平滑：训练分布规则在更长序列上自然延续",
            "远距离先验压制长程检索，任务适配不如 RoPE",
        ],
        "followUps": [
            {"q": "ALiBi 和 RoPE 能同时用吗？", "a": "可以叠加（logits 上既有旋转相对项又有距离惩罚），部分模型在超长上下文实验里这么做过以抑制远处噪声；但要重新调斜率，一般不作为默认组合。"},
        ],
    },
    {
        "id": "transformer-021",
        "topic": "位置编码",
        "type": "八股",
        "difficulty": 4,
        "frequency": 3,
        "companies": ["阿里", "零一万物", "微软"],
        "years": ["2024", "2025"],
        "question": "把 RoPE 的长上下文扩展方法讲一遍：位置插值、NTK-aware、YaRN 各自的思路和差别是什么？",
        "answerMd": r'''**一句话核心**：三种方法都是在「不重训或少量微调」的前提下改 RoPE 的频率/位置标度——PI 把位置整体压缩进训练范围，NTK-aware 调大 base 让低频维度自然适应更长距离，YaRN 按频率分段处理并修正注意力温度，效果与所需微调量依次更优。

**1. 位置插值（PI）。** 把推理时的位置 $m$ 缩成 $m \cdot L_{train}/L_{target}$，所有频率统一压缩，等效于把「整张位置尺」塞回训练范围。只需少量长文本微调（论文用千步级）即可扩展，但高频维度被过度压缩，近距离区分度受损。

**2. NTK-aware 缩放。** 观察：高频维度（负责近距离）不该压，低频维度（负责远距）才需要延伸。做法是改 RoPE 的 base：$b' = b \cdot s^{d/(d-2)}$（$s$ 是扩展倍数），等效于「高频维度几乎不插值、低频维度插值更多」的非线性插值，也叫「外推补插值」。常可零微调先顶一段，再少量微调。

**3. YaRN。** 更精细：按维度频率用 ramp 函数分段——高频维不插值（保持分辨率）、低频维全插值（覆盖长距）、中间平滑过渡；再配一个随 $s$ 增大的注意力温度修正，抵消长上下文下注意力 logits 平均值漂移带来的分布变尖。相同微调预算下质量更好，成为主流扩展配方之一。

**4. 补充。** LongRoPE 用进化搜索对每个维度找非均匀缩放并做渐进式扩展（论文报告可到百万级 token）；工程上的通用原则是：扩展倍数越大，越需要分阶段训练 + 长数据，纯免训练方案只适合小倍数（2~4 倍）。''',
        "keyPoints": [
            "PI：位置整体乘 s 分之一，塞回训练范围，需少量微调",
            "NTK-aware：调大 base，高频不压低频多压，可近零微调",
            "YaRN：按频率分段插值 + 注意力温度修正，同预算效果最好",
            "LongRoPE：逐维非均匀缩放 + 渐进扩展，可达百万级",
            "倍数越大越需要分阶段训练与长文本数据",
        ],
        "followUps": [
            {"q": "为什么高频维度不能压缩？", "a": "高频子空间角度随位置变化快，负责区分相邻 token；压缩后相邻位置的相位差变小，近距离位置分辨力下降，表现为局部语法与短程检索变差。YaRN 的 ramp 就是为了保住这些维度。"},
        ],
    },
    {
        "id": "transformer-022",
        "topic": "位置编码",
        "type": "场景",
        "difficulty": 4,
        "frequency": 3,
        "companies": ["阿里", "字节", "月之暗面"],
        "years": ["2025", "2026"],
        "question": "给你一个训好的 8K 上下文 LLM，要扩到 128K，给出完整方案：数据、训练课程、结构与评测分别怎么做？",
        "answerMd": r'''**一句话核心**：先调 RoPE（放大 base 或 YaRN 式缩放），再用「短到长渐进 + 长数据配比」的分阶段续训，配合序列并行撑显存，最后用检索类基准而非困惑度验收。

**1. 结构先行。** 128K/8K = 16 倍，直接用会崩；先做 RoPE base 调整（如把 base 提到 5e5~1e6 量级，或按 YaRN/NTK 分段缩放），若模型有全局/局部混合层则按目标长度重新标定窗口。训练侧上序列并行/上下文并行把 128K 的激活和注意力分摊到多卡，注意力显存靠 FlashAttention。

**2. 数据。** 需要真实长依赖语料：书籍、长代码仓库、多轮超长对话、长文档问答对；纯短样本拼接（不隔断的 packing）不够，要用原生长样本并提高其占比；同时保留一部分短数据防能力回退。数据量不需要从头训那么大，数十 B token 量级的续训是常见量级。

**3. 训练课程。** 渐进式：8K 短恢复 → 32K → 128K，每阶段几百到上千步、学习率小（如峰值 1e-5 以下）带短暂 warmup，长度跳变太大容易 loss 不稳；也可与退火阶段（高质量数据）合并做。

**4. 评测。** 困惑度在长文档上只作参考，必须测能力：大海捞针（多深度、多位置、多针）、RULER 类合成检索、长文档 QA、代码仓库级补全、调用长上下文的应用评测；同时回归短上下文基准确认没退化。最后校准服务侧：128K 的 KV 显存与 prefill 时延，决定是否开稀疏/滑窗或 KV 量化。''',
        "keyPoints": [
            "先改 RoPE（base 放大/YaRN），16 倍扩展不能只靠微调",
            "渐进课程：8K 恢复 → 32K → 128K，小学习率防不稳",
            "数据以原生长样本为主（书/仓库/长对话），保留短数据防回退",
            "训练要上序列并行 + FlashAttention 才放得下长序列",
            "验收看检索类基准与短域回归，不看困惑度",
        ],
        "followUps": [
            {"q": "为什么不能一步直接在 128K 上练？", "a": "位置编码分布突变、注意力统计量漂移，容易 loss 飙升且样本效率低；渐进课程让模型先在中等长度建立新的位置刻度，再往更长推，每一步都在已适应范围内插值式扩展。"},
        ],
    },
    # ---------------------------------------------------------------- 结构细节
    {
        "id": "transformer-023",
        "topic": "结构细节",
        "type": "八股",
        "difficulty": 3,
        "frequency": 5,
        "companies": ["字节", "阿里", "腾讯", "百度"],
        "years": ["2023", "2024", "2025"],
        "question": "Pre-LN 和 Post-LN 有什么区别？为什么如今大模型几乎都用 Pre-LN？",
        "answerMd": r'''**一句话核心**：Post-LN 在残差之后做归一化（LN 挡在梯度主路上），深了难训、依赖 warmup；Pre-LN 把 LN 放在子层输入侧、残差是干净的恒等通道，梯度稳定、对深网络和 warmup 都友好，因此成为 LLM 默认，代价是输出需要补一个 final LN。

**1. 结构差异。** 原版 Transformer 是 Post-LN：$x = \mathrm{LN}(x + \mathrm{Sublayer}(x))$，每个残差出口都过一次 LN；Pre-LN 是 $x = x + \mathrm{Sublayer}(\mathrm{LN}(x))$，LN 只在子层内部，主干本身没有算子。梯度上，Post-LN 的反向每层都要穿过 LN（且早期 LN 对梯度有缩放/相关效应），深层堆叠时梯度方差难以控制，原始论文为此用 LR warmup；Pre-LN 的恒等通道让梯度和信息无损直达底层，100 层也能稳训。

**2. 性能权衡。** 有分析认为 Post-LN 训好后每层贡献更均衡、某些任务上限略高，但训练代价大；Pre-LN 早期层与深层梯度尺度不一致（底层更新相对小），可以通过 final LN、residual 缩放或 DeepNorm 类变体缓解。GPT-2 之后的主流 LLM（Llama/Qwen/DeepSeek）都是 Pre-RMSNorm + final RMSNorm。

**3. 相关变体。** Sandwich-LN（子层前后各一次）、Peri-LN 等继续在「归一化放哪」上做文章；还有把 LN 换 RMSNorm 省均值计算、在 Q/K 上加 Norm 控 logits 等，都属于同一主题的工程演进。面试时能给出两条公式、解释恒等梯度通路、点名 final LN 的必要性即可。''',
        "keyPoints": [
            "Post-LN：LN 在残差出口，梯度每层过 LN，深训难、依赖 warmup",
            "Pre-LN：LN 只在子层内，残差是恒等高速路，梯度稳定",
            "Pre-LN 输出分布会漂移，必须加 final LN",
            "主流 LLM = Pre-RMSNorm + final RMSNorm",
            "Sandwich/Peri 等变体继续优化归一化位置",
        ],
        "followUps": [
            {"q": "为什么 Pre-LN 模型底层参数更新偏慢？", "a": "越靠近输出层的分支梯度越「新鲜」，恒等通路把梯度原样传到底层，但底层子层的有效梯度经过了更多层的缩放分配，相对小；表现为底层学习偏慢，可用逐层学习率或调整残差缩放缓解。"},
        ],
    },
    {
        "id": "transformer-024",
        "topic": "结构细节",
        "type": "八股",
        "difficulty": 3,
        "frequency": 5,
        "companies": ["字节", "阿里", "DeepSeek", "面壁智能"],
        "years": ["2023", "2024", "2025"],
        "question": "FFN 为什么从 ReLU 演进到 SwiGLU？SwiGLU 的隐层维度为什么要设成 8/3 倍？",
        "answerMd": r'''**一句话核心**：FFN 演进主线是「引入平滑激活与门控乘性交互」——ReLU → GELU → GLU 门控族 → SwiGLU（Swish 门控 + 线性支路），同等参数下质量更稳更好；为与原 $4d$ FFN 参数量对齐，三条 $d \to h$ 矩阵的 SwiGLU 把 $h$ 设为 $\frac{8}{3}d$。

**1. FFN 的角色。** 注意力负责「token 间混信息」，FFN 负责「token 内做非线性变换与知识存取」，参数占一层的三分之二，是容量主体。

**2. 激活演进。** ReLU 有死区、分段线性；GELU 平滑（GPT/BERT 采用）带来稳定的小幅提升。真正质变是 GLU 族：把一个线性支路 $xW_3$ 作为门，与激活支路相乘——$\mathrm{FFN}(x) = (\mathrm{Swish}(xW_1) \otimes xW_3) W_2$。乘性门控让「传多少信息」变成依输入而定的乘法调制，比单支路非线性表达更强，实验上 SwiGLU 在同算力下最稳，成为 Llama/Qwen/DeepSeek 等的标配。

**3. 8/3 的来历。** 原版 FFN 隐层 $4d$，参数 $2 \cdot d \cdot 4d = 8d^2$；SwiGLU 有三个矩阵（两个 $d \to h$、一个 $h \to d$），参数 $3dh$。令 $3dh = 8d^2$ 得 $h = \frac{8}{3}d \approx 2.67d$，即「同参数对比」的公平设置；实现里通常再向上取整到 256 的倍数以利张量并行切分（如 $d=4096$ 时取 11008 一类的值）。

**4. 追问延伸。** Swish 即 $\mathrm{SiLU}(x) = x \cdot \sigma(x)$，处处非零、平滑可微；也有工作比较 GeGLU/ReGLU，结论差异不大，关键在门控结构本身。''',
        "keyPoints": [
            "FFN 是 token 内非线性变换与知识存取的容量主体",
            "GELU 解决 ReLU 死区；GLU 族引入乘性门控",
            "SwiGLU = Swish(xW1) ⊗ xW3 再 W2，同算力质量最稳",
            "三条矩阵对齐原 4d FFN 参数：h = 8/3 d，实现取 256 倍数",
        ],
        "followUps": [
            {"q": "MoE 里的专家和 FFN 是什么关系？", "a": "MoE 就是把每层的单个 FFN 换成多个并列 FFN（专家）加一个路由器，每个 token 只激活 top-k 个专家的 FFN，本质是对 FFN 容量做条件计算扩展。"},
        ],
    },
    {
        "id": "transformer-025",
        "topic": "结构细节",
        "type": "八股",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["面壁智能", "智谱", "阿里"],
        "years": ["2023", "2024", "2025"],
        "question": "输入 embedding 和输出 lm_head 要不要共享权重？大模型为什么常常不共享？",
        "answerMd": r'''**一句话核心**：共享（tied）能省一份 $V \times d$ 参数、对小模型和小数据有利；但当词表大、模型大时，输入 embedding 是「查表」而输出层是「全词表判别」，功能差异变大且参数占比可忽略，主流大模型选择不共享（untied）。

**1. 共享的收益。** 词表 $V$ 十几万、宽度 $d$ 几千时，embedding 矩阵有数亿参数：GPT-2、早期小模型共享后参数明显变小，且输入输出在同一语义空间，小数据下有正则效果；很多小尺寸模型（Gemma 2B/9B 级等）保持 tied。

**2. 不共享的理由。** 一是功能不对称：输入侧只取自身 token 的行，输出侧要做 $V$ 类 softmax 判别，输出层需要更高秩、更任务化的表示，绑定会互相牵制；二是绝对开销下降：7B 模型的 embedding 约 0.5~1B 参数，占比不到 15%，省不了多少；三是有分析指出输出层希望与输入层「对偶」而非「相同」，绑定在大词表下甚至可能引入噪声。Llama 全系 untied，Qwen 只在小尺寸型号上 tied，都是这一权衡的体现。

**3. 实操注意。** tied 时 logit 是 $\frac{h W_E^\top}{T}$（T 为温度），embedding 的 norm 会直接影响输出分布；扩词表（CPT 场景）时要注意同步处理两边；评测 embedding 质量时，tied 模型不能直接拿 lm_head 当句向量用。''',
        "keyPoints": [
            "tied 省 V*d 参数，小模型/小数据下有正则收益",
            "输入是查表、输出是全词表 softmax 判别，功能不对称",
            "大模型中 embedding 参数占比小，绑定收益低、约束表达",
            "Llama 系 untied；部分小尺寸型号仍 tied",
        ],
        "followUps": [
            {"q": "tied 模型推理时 logits 计算有什么特点？", "a": "lm_head 直接复用 embedding 矩阵转置，不用存第二份权重；embedding 的行范数差异会直接体现在 logit 尺度上，因此 tied 模型对 embedding 归一化与温度更敏感。"},
        ],
    },
    {
        "id": "transformer-026",
        "topic": "结构细节",
        "type": "八股",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["字节", "百度", "腾讯"],
        "years": ["2023", "2024"],
        "question": "残差连接为什么重要？除了标准残差，还有哪些围绕它做训练稳定的改造？",
        "answerMd": r'''**一句话核心**：残差给网络一条恒等梯度高速路，让「加深」不再退化为优化难题——梯度可无损直达浅层、每层只需学增量修正；围绕它的改造包括初始化缩放、ReZero/LayerScale、DeepNorm 与归一化位置调整。

**1. 为什么必须。** 没有残差时，反向传播是多层非线性函数的连乘，深网络梯度衰减/爆炸且各层耦合；有残差时 $x_{l+1} = x_l + F(x_l)$，$\partial x_{l+1}/\partial x_l = I + \partial F/\partial x_l$，恒等项保证梯度主路至少原样通过，网络等效为「学习残差增量」的集成结构，深而稳。信息层面，底层特征可以直达顶层，注意力/FFN 只需建模残差修正。

**2. 常见改造。** 一是初始化缩放：GPT-2 把残差分支输出乘 $1/\sqrt{2N}$，控制残差流方差随深度增长；二是 ReZero（$x + \alpha F(x)$，$\alpha$ 初始化 0）与 LayerScale（逐通道可学习小系数），让每层从「不干预」学起，深 Transformer 不用 warmup 也能训；三是 DeepNorm 放大残差分支并相应缩放初始化，可训千层；四是 Pre-LN/Post-LN 之争本质也是残差路径上放不放 LN。

**3. 与 LLM 的联系。** 残差流的「宽度-深度」容量观（特征以叠加形式写入残差流）也是解读大模型行为（如 residual stream 视角的可解释性研究）的基础；工程上残差 dropout 位置（分支内 vs 出口）也影响正则强度。''',
        "keyPoints": [
            "恒等映射让梯度无损回传，深层可训",
            "每层学增量修正，等效集成结构",
            "GPT-2 用 1/sqrt(2N) 缩放残差分支初始化",
            "ReZero/LayerScale 让层从零贡献学起，深网免 warmup",
            "DeepNorm 可训上千层；Pre/Post-LN 是残差路径的变体",
        ],
        "followUps": [
            {"q": "残差流方差为什么会随深度增长？", "a": "每层向流里加一个独立分支输出，方差近似相加；若不缩放初始化，L 层后流方差线性增长，导致注意力 logits 与 LN 外的激活过大。这就是 GPT-2 缩放与 QK-Norm 要解决的问题。"},
        ],
    },
    {
        "id": "transformer-027",
        "topic": "结构细节",
        "type": "八股",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["智谱", "阿里", "华为"],
        "years": ["2024", "2025"],
        "question": "LayerNorm、RMSNorm 有什么区别？为什么 LLM 都改用 RMSNorm，QK-Norm 又是干什么的？",
        "answerMd": r'''**一句话核心**：RMSNorm 砍掉 LayerNorm 的均值中心化、只做「除以均方根 + 逐维缩放」，效果几乎不降、计算更省，成为 LLM 默认；QK-Norm 是把 RMSNorm 用在注意力的 Q/K 上（沿头维度），用来钳制 logits 增长、稳定训练。

**1. 公式对比。** LayerNorm：$y = g \cdot \frac{x - \mu}{\sqrt{\sigma^2 + \epsilon}} + b$，先减均值再除标准差；RMSNorm：$y = g \cdot \frac{x}{\sqrt{\frac{1}{d}\sum x_i^2 + \epsilon}}$。差异只在去均值——LN 的不变性来源主要是「方向归一 + 尺度缩放」，中心化的贡献实验上很小，于是 RMSNorm 用更少的算子（少一次均值与一次减法）拿到几乎相同的效果，在大模型规模下省的时间不可忽视。

**2. 为什么 LLM 采用。** 一是省计算与访存（LN 在残差流上每个 block 两次，序列长时开销可观）；二是没有 batch 维依赖，训练推理一致；三是配合 Pre-LN 结构已被验证可扩展。代价理论上是对「均值偏移」类扰动不变性减弱，实践中没成为问题。

**3. QK-Norm。** 把 RMSNorm 应用到每个头的 Q、K 向量上（在 RoPE 之前），使点积 logits 的幅度被限制在 $\sqrt{d_k}$ 量级，防止训练后期 logits 无界增长导致的 softmax 塌缩与数值不稳；Gemma 2、Qwen 3 等模型采用（Qwen 3 同时移除了 QKV bias，用 QK-Norm 替代其稳定作用）。与它同主题的还有 logit soft-capping（Gemma 2 对注意力和输出 logits 做软截断）。''',
        "keyPoints": [
            "LN 去均值 + 除标准差；RMSNorm 只除均方根 + 缩放",
            "RMSNorm 计算更少、效果几乎不变，成为 LLM 默认",
            "无 batch 依赖，训练推理行为一致",
            "QK-Norm 沿头维归一 Q/K，钳制注意力 logits 增长",
            "同族手段：logit soft-capping、可学习温度",
        ],
        "followUps": [
            {"q": "为什么不用 BatchNorm？", "a": "BN 依赖 batch 统计，序列任务的 batch 内样本相关性高、且训练推理统计不一致，变长序列与小 batch 大模型下更不稳；LN/RMSNorm 按样本内归一，天然规避这些问题。"},
        ],
    },
    {
        "id": "transformer-028",
        "topic": "结构细节",
        "type": "八股",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["面壁智能", "零一万物", "智谱"],
        "years": ["2023", "2024", "2025"],
        "question": "参数量固定的情况下，模型应该做得更深还是更宽？设计时有哪些工程约束？",
        "answerMd": r'''**一句话核心**：理论倾向「在优化允许的范围内适当偏深」，但受梯度稳定性、串行时延与并行切分约束，主流 LLM 的宽深比（$d/L$）大致落在 100~130 附近；这不是纯科学问题，而是与 TP/PP、MFU 一起折衷的工程决策。

**1. 为什么偏深有理。** 同参数下更深往往样本效率更高、loss 略低（深度换表达）；Scaling Laws 用「参数量 N=12Ld^2」聚合了深宽，等效意义上两者可互换，但在数据充足的预训练里适度深的配置通常略优。

**2. 现实约束。** 一是优化与稳定：层数多则梯度路径长，Pre-LN 缓解但底层更新慢的问题仍在；二是时延与并行：层是串行的，流水线并行切层、推理 decode 每步都要走完所有层，太深拖延迟；TP 要求 $d$ 和头数能被 TP 度整除，PP 要求层数能被 stage 整除；三是激活显存与重计算成本随层数线性增。四是头维度下限（$\ge 64$）限制了「太宽头太多」的无意义配置。

**3. 经验值。** GPT-3 175B 是 96 层 × 12288（比值 128）；Llama 系 7B 是 32 层 × 4096（128）；更小模型比值会降低（层数下不来太多）。若被追问「能不能 8 层做 7B」，可以答：技术上可行（超宽 + 强并行），但样本效率与质量通常吃亏，且单层注意力/FFN 巨大导致 TP 通信放大，一般不做。''',
        "keyPoints": [
            "参数 N ≈ 12*L*d^2，深宽在一定范围内可互换",
            "适度偏深样本效率更高，但受优化与稳定性限制",
            "串行层数影响 PP/decode 时延，d 与头数要能被 TP 整除",
            "主流 LLM 的 d/L 比值约 100~130",
            "太宽的单层会放大 TP 通信与激活显存",
        ],
        "followUps": [
            {"q": "更细粒度上，头数、FFN 比例这些怎么和深宽联动？", "a": "头数 = d/d_k 且 d_k 不小于 64，宽模型自然头多；FFN 隐层按 8/3 d 随宽度走。先定参数量与层数（考虑 PP/TP 约束），再反推 d、头数与 FFN，是常见的自上而下设计顺序。"},
        ],
    },
    # ---------------------------------------------------------------- KVCache与推理优化
    {
        "id": "transformer-029",
        "topic": "KVCache与推理优化",
        "type": "八股",
        "difficulty": 3,
        "frequency": 5,
        "companies": ["字节", "阿里", "腾讯", "华为"],
        "years": ["2024", "2025"],
        "question": "KV Cache 为什么能加速解码？估算一下：7B 模型、GQA 8 个 KV 头、fp16，32K 上下文一条请求要多少 KV 显存？",
        "answerMd": r'''**一句话核心**：解码时历史 token 的 K/V 不变，缓存后每步只算新 token 的 Q 与全量 K/V 的一次点积，避免整段重算；KV 显存 = $2 \times L \times n_{kv} \times d_{head} \times T \times \mathrm{bytes}$，本例约 8GB/条。

**1. 原理。** 自回归生成第 $t$ 步时，前 $t-1$ 个 token 的 K、V 与历史完全一致（自注意力只依赖自身与前文）。无 cache 时每步要重算全部 K/V，注意力计算 $O(t^2)$；有 cache 后每步只投影 1 个新 token 得到 $(q_t, k_t, v_t)$，把 $k_t, v_t$ 追加进 cache，注意力变成 1 个 query 对 $t$ 个 key 的计算，$O(t)$。代价是显存随上下文线性增长，且 decode 每步都要把整份 KV 从显存读一遍——是 memory-bound 的。

**2. 显存估算。** 公式：每 token 每层存 K、V 两组，各 $n_{kv}$ 个头 × $d_{head}$ 维。代入：$2 \times 32 \text{层} \times 8 \text{头} \times 128 \text{维} \times 2\text{字节} = 131072$ 字节 ≈ 128KB/token。32K 上下文 → $32768 \times 128\text{KB} = 4$GB。若是没有 GQA 的 MHA（32 头）则为 512KB/token、32K 达 16GB；batch 8 就是 32GB，直接说明 GQA 与 KV 量化（fp8 可再省一半）的必要性。对比权重：7B fp16 约 14GB——长上下文下 KV 会反超权重，成为显存与带宽的主要消耗。

**3. 引申。** 由此推出整个推理优化栈的动机：GQA/MLA 压 KV、PagedAttention 管碎片、prefix caching 复用公共前缀、continuous batching 提带宽利用率，都是围绕这份线性增长的 KV 做文章。''',
        "keyPoints": [
            "历史 K/V 不变可缓存，decode 每步 O(t) 而非 O(t^2)",
            "公式：2 * 层数 * n_kv * d_head * T * bytes",
            "例：32 层/8 头/128 维/fp16 = 128KB/token，32K = 4GB",
            "MHA 同配置是 4 倍，长上下文 KV 反超权重",
            "decode 是带宽瓶颈，一切优化围绕 KV 做文章",
        ],
        "followUps": [
            {"q": "prefill 和 decode 的性能瓶颈分别是什么？", "a": "prefill 一次算整段 prompt，计算密集（compute-bound），指标是 prefill 吞吐；decode 每步 1 个 token、要读全部权重和 KV，访存密集（memory-bound），指标是单流延迟与并发吞吐。两者常被拆成不同阶段调度。"},
        ],
    },
    {
        "id": "transformer-030",
        "topic": "KVCache与推理优化",
        "type": "八股",
        "difficulty": 4,
        "frequency": 4,
        "companies": ["字节", "阿里", "华为", "NVIDIA"],
        "years": ["2024", "2025"],
        "question": "vLLM 的 PagedAttention 解决了什么问题？分页管理是怎么做的，为什么能大幅提高吞吐？",
        "answerMd": r'''**一句话核心**：PagedAttention 把操作系统的虚拟内存分页思想搬到 KV Cache——按固定大小的 block 存 KV、用页表映射逻辑位置，消除按最大长度预分配造成的内外部碎片与重复存储，把显存利用率从两三成提到九成以上，论文报告吞吐数倍提升。

**1. 原有痛点。** 传统实现给每条请求预分配「最大序列长度 × 全 batch」的连续 KV 缓冲：请求实际只用到 200 token 却按 2048 预留（内部碎片）；不同请求长度不一，释放后再分配产生外部碎片；束搜索/并行采样等共享前缀的场景还要各自复制整份 KV。实测大量显存被浪费，能开的并发因此受限。

**2. 分页怎么做。** KV 按 block（如 16 个 token）切块，逻辑序列由页表索引到物理 block，block 可不连续；按需分配、用多少占多少，浪费只剩每请求最后一个半空 block（小于 4%）。前缀相同的请求通过页表指向同一批物理 block 实现共享；fork（束搜索、多次采样）用引用计数 + 写时复制（copy-on-write），只有分叉的新 token 才写新块。

**3. 为什么快。** decode 是访存瓶颈，显存省下来就能同时塞更多请求，continuous batching 配合让 GPU 带宽始终打满；分页还让「抢占与换出」（把低优先请求 KV 换到 CPU）成为可能。面试延伸：该思想已被各推理引擎吸收为标配，配套还有 chunked prefill、prefix caching、KV 量化；也可对比 SGLang 的 RadixAttention（前缀树复用）。''',
        "keyPoints": [
            "痛点：按 max_len 预分配导致内部/外部碎片与重复 KV",
            "按 block 分页 + 页表映射，浪费降到最后一个半空块",
            "引用计数 + copy-on-write 支持前缀共享与束搜索",
            "显存利用率提升 → 并发提升 → 吞吐数倍（memory-bound 收益放大）",
            "后续演进：chunked prefill、prefix caching、KV 量化",
        ],
        "followUps": [
            {"q": "分页会不会拖慢注意力计算？", "a": "block 在物理上要求连续、大小固定，内核按 block 索引表访存，比连续 buffer 多一次间接寻址，但 KV 读取本来就是流式的，开销很小；工程上收益远大于代价。"},
        ],
    },
    {
        "id": "transformer-031",
        "topic": "KVCache与推理优化",
        "type": "八股",
        "difficulty": 3,
        "frequency": 4,
        "companies": ["字节", "阿里", "快手"],
        "years": ["2024", "2025"],
        "question": "什么是 continuous batching？它比静态 batching 好在哪，为什么 decode 阶段特别需要它？",
        "answerMd": r'''**一句话核心**：continuous batching（iteration-level batching）把调度粒度从「整条请求」细化到「每次前向迭代」——每步动态加入新请求、移除完成请求，让 batch 始终是满的；它治的是静态 batching 的「长尾等待」问题，在 decode 这种访存受限的阶段收益最大。

**1. 静态 batching 的问题。** 请求按组凑批、整组同进同出：同一 batch 里有的请求生成 10 token、有的生成 500 token，短请求结束后其显存与算力空转，直到最长的做完才换下一组；吞吐低、排队延迟大，显存也无法随请求增减弹性伸缩。

**2. continuous batching 怎么做。** 调度器在每次模型前向（一个 iteration）后检查：完成的请求立刻退出、释放 KV，等待队列的请求立刻插入；prefill 与 decode 可以分池调度或用 chunked prefill 混合，保证每步都有活干。Orca（OSDI 2022）最早提出 iteration-level 调度与选择性批处理，vLLM 等将其变成工业标配。

**3. 为什么 decode 特别受益。** 单流 decode 每步只处理 1 个 token，GPU 的算力大量空转，瓶颈在读权重/KV 的带宽；把几十条请求的 decode 塞进同一个前向，权重读取被分摊，单步耗时几乎不变而产出翻几十倍。所以评估推理服务要看「并发下吞吐」与「首 token 延迟/每 token 延迟」的权衡曲线，continuous batching 正是这条曲线的调节器。''',
        "keyPoints": [
            "调度粒度从请求级细化为迭代级，进出 batch 动态化",
            "静态 batch 有长尾空转，显存与算力双重浪费",
            "decode 访存受限，批处理几乎白拿吞吐（权重读取分摊）",
            "与 PagedAttention、chunked prefill 配合形成现代推理栈",
            "核心权衡：吞吐 vs 首 token/每 token 延迟",
        ],
        "followUps": [
            {"q": "prefill 和 decode 混批会有什么问题？", "a": "prefill 是计算密集的长序列前向，混入 decode 批会拉长该迭代耗时，恶化在线 decode 延迟；解法是分开调度（两池）、chunked prefill 把长 prompt 切片穿插，或按 SLO 分优先级队列。"},
        ],
    },
    {
        "id": "transformer-032",
        "topic": "KVCache与推理优化",
        "type": "八股",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["字节", "阿里", "腾讯"],
        "years": ["2024", "2025"],
        "question": "prefix caching（前缀缓存）是怎么工作的？什么条件下能命中，和多轮对话的关系是什么？",
        "answerMd": r'''**一句话核心**：prefix caching 把「相同 token 前缀」的 KV 存下来复用——新请求只需对多出的后缀做 prefill；命中条件是前缀逐 token 一致（位置编码与内容都相同），它把系统提示词、few-shot、多轮对话历史这类重复前缀的 TTFT 大幅降低。

**1. 机制。** 以 SGLang 的 RadixAttention 为例：用 radix 树按 token 序列组织 KV 块，树路径即前缀；请求到来时沿树匹配最长已缓存前缀，直接复用对应 KV 块，只计算剩余部分；缓存命中块有引用计数，未命中按 LRU 逐出。vLLM 的 automatic prefix caching 思路类似（按块哈希）。

**2. 命中条件。** 一是逐 token 完全相同（一个字不同则从那以后全部失效）；二是位置对齐——前缀必须从位置 0 开始（位置编码依赖绝对位置，RoPE 下同理），所以只有「公共开头」能复用，插入到中间的内容不行；三是采样温度等不影响 KV，但 chat template 里时间戳、随机 id 等动态字段会破坏命中，模板设计要避免把变化内容放在前缀里。

**3. 收益场景。** 固定 system prompt + few-shot 的 API 服务、多轮对话（每轮复用之前所有轮次的 KV）、批量评测同前缀样本、Agent 循环里反复携带的长工具说明。多轮对话是最大受益者：第 k 轮只需 prefill 最新一轮的增量，TTFT 与算力开销随轮次近似不变。''',
        "keyPoints": [
            "radix 树/块哈希组织 KV，按最长公共前缀复用",
            "逐 token 一致且从位置 0 开始才命中",
            "动态字段（时间戳/随机 id）放进前缀会破坏缓存",
            "多轮对话、固定 system prompt、Agent 循环是主要收益场景",
            "配合 LRU 逐出与引用计数管理显存",
        ],
        "followUps": [
            {"q": "命中前缀缓存后,后续 token 的 KV 还要算吗？", "a": "要。复用的只是前缀的 KV；新生成的每个 token 在每层都要追加自己的 K/V。缓存省的是对旧前缀的重复 prefill 计算，不是免去增量计算。"},
        ],
    },
    {
        "id": "transformer-033",
        "topic": "KVCache与推理优化",
        "type": "八股",
        "difficulty": 4,
        "frequency": 4,
        "companies": ["字节", "智谱", "月之暗面", "OpenAI"],
        "years": ["2024", "2025"],
        "question": "投机解码（speculative decoding）为什么能保证输出分布不变？期望接受多少个 token，加速比由什么决定？",
        "answerMd": r'''**一句话核心**：小 draft 模型连猜 $\gamma$ 个 token，大模型一次前向并行验证并用拒绝采样校正——接受/拒绝的概率设计保证最终输出分布与单独用大模型完全一致；期望每轮产出约 $\frac{1-\alpha^{\gamma+1}}{1-\alpha}$ 个 token，加速比取决于接受率 $\alpha$ 与 draft/verify 的开销比。

**1. 流程。** draft 模型（小几倍到几十倍）自回归地生成 $\gamma$ 个候选；target 模型对「前缀 + 候选」做一次并行前向，得到每个位置的分布；从左到右逐个做拒绝采样：若 draft 采样 token 的概率比 $p/q$ 满足接受条件则接受，否则以 $1 - p/q$ 拒绝并改由 target 分布重采样，之后 draft 重新开始。数学上该拒绝采样使每个位置的边缘分布恰为 target 分布，所以是无损加速。

**2. 收益公式。** 设单位置接受率为 $\alpha$，一轮期望产出 $E = \frac{1-\alpha^{\gamma+1}}{1-\alpha}$（最后一轮验证还白送一个正确 token）。$\alpha=0.8, \gamma=4$ 时约 3.4；加速比还要乘以「verify 一步几乎不比 decode 一步贵」这个条件——decode 是访存受限的，多算几个 token 的 logits 增量很小，这是投机解码成立的物理前提。

**3. 工程要点。** draft 与 target 词表必须一致；$\gamma$ 是延迟-浪费权衡（拒绝越多浪费越大）；接受率随任务变化（代码 > 开放对话），可用温度、动态 $\gamma$ 缓解。变体里 Medusa 用多输出头省掉独立 draft 模型，EAGLE 在特征层做自回归 draft，接受率更高。''',
        "keyPoints": [
            "拒绝采样校正使输出分布与 target 严格一致（无损）",
            "期望产出 (1-α^(γ+1))/(1-α)，α 是单位置接受率",
            "前提：decode 访存受限，并行验证的边际成本很小",
            "γ 越大潜在收益大但被拒浪费也大，需动态调节",
            "Medusa/EAGLE 变体去掉独立 draft、提高接受率",
        ],
        "followUps": [
            {"q": "什么场景投机解码会负优化？", "a": "接受率低（高温度采样、创意写作、多语言混杂、target 与 draft 能力差距过大）时，draft 生成的 token 大量被拒，白白多算；batch 已经很大、GPU 算力打满时验证的算力开销也不再免费，收益会缩水甚至为负。"},
        ],
    },
    {
        "id": "transformer-034",
        "topic": "KVCache与推理优化",
        "type": "八股",
        "difficulty": 4,
        "frequency": 3,
        "companies": ["月之暗面", "智谱", "字节"],
        "years": ["2024", "2025"],
        "question": "Medusa 和 EAGLE 这两类投机解码变体分别怎么构造 draft？EAGLE 为什么接受率更高？",
        "answerMd": r'''**一句话核心**：Medusa 在 target 模型顶层挂多个解码头，直接并行预测未来 k 个位置的 token，用树形注意力验证；EAGLE 在「特征层」做自回归——draft 头读取 target 最后一层隐藏状态预测下一个特征再映射成 token，复用 target 的 KV 与表征，分布偏移小、接受率显著更高。

**1. Medusa。** 不引入独立 draft 模型：在主干上训练 k 个额外头，第 i 个头预测「往后第 i 个」token；单个头置信度不高，因此取各头 top-k 组成树形候选，用 tree attention（把树路径编码成 mask 一次前向验证）。优点是训练便宜、部署简单；缺点是「一步预测多步」误差累积快，接受长度有限。

**2. EAGLE。** 关键观察：token 级自回归误差大，而 hidden state 已高度确定。EAGLE 的 draft 头以「target 的特征 + 上一步 token 的 embedding」为输入自回归地预测下一步特征，再过 target 的 lm_head 得到 token；因为每步都建立在 target 前向给出的真实特征上（而不是自己的历史），训练/推理分布更一致，接受率与期望长度更高（论文报告相对标准投机解码还有倍数级提升，EAGLE-2 加上下文感知的动态树，EAGLE-3 融合多层特征）。代价是要训练一个 draft 头模块并保留 target 主干前向。

**3. 对比总结。** 有同源小模型 → 传统 draft 即可；无现成小模型、要求高质量接受率 → EAGLE 系；要低成本快速部署 → Medusa。三者共享同一套树形验证与接受准则，可互换组合。''',
        "keyPoints": [
            "Medusa：顶层多头并行预测未来 k 步 + 树形注意力验证",
            "Medusa 一步看多步、误差累积，接受长度有限",
            "EAGLE：在 hidden state 上自回归 draft，复用 target KV 与表征",
            "EAGLE 每步以 target 真实特征为条件，分布一致、接受率高",
            "EAGLE-2/3 用动态树与多层特征继续提升",
        ],
        "followUps": [
            {"q": "树形候选是怎么一次验证的？", "a": "把候选组织成一棵树，树上每条根到叶路径是一个候选序列；tree attention 用自定义 mask 保证每个候选 token 只注意自己路径上的祖先，一次前向同时得到所有路径各位置的分布，再沿树逐层做接受/拒绝。"},
        ],
    },
    {
        "id": "transformer-035",
        "topic": "KVCache与推理优化",
        "type": "手撕",
        "difficulty": 4,
        "frequency": 4,
        "companies": ["字节", "阿里", "快手"],
        "years": ["2024", "2025"],
        "question": "手写一个带 KV Cache 的自回归解码循环（支持 GQA），说明 prefill 与 decode 两个阶段的区别。",
        "answerMd": r'''**一句话核心**：prefill 对整段 prompt 一次前向、写出全部 KV 并得到首个 logits；decode 每步只喂 1 个新 token，把新 K/V 追加进 cache，用 GQA 展开后再算注意力。

核心是 cache 的生命周期：每层独立维护 K/V 两个张量，形状 (B, n_kv_heads, T, d_head)；每步沿序列维拼接追加。注意真实系统不会逐层 cat（会反复拷贝 O(T)），而是预分配环形缓冲或分页块，这里为了教学清晰用 cat 表意。GQA 的展开用 repeat_interleave 把 n_kv 组复制到 n_heads。decode 阶段一次只有 1 个 query，注意力输出对该 query 归一化，无需因果 mask（新 token 本来就在最后）。''',
        "keyPoints": [
            "prefill：整段一次前向，生成全部 KV 与首个 logits",
            "decode：每步 1 个新 token，追加 K/V 后算 1 对 t 的注意力",
            "GQA 用 repeat_interleave 把 KV 组复制到查询头数",
            "真实实现用预分配/分页缓冲避免反复 cat 拷贝",
            "decode 无需 causal mask（单 query 位于序列末端）",
        ],
        "followUps": [
            {"q": "KV Cache 什么时候会失效需要重算？", "a": "换模型/换量化格式、前缀缓存被逐出、采样中途修改已生成内容、beam 分叉重排、以及 window attention 滑出窗口的旧 token；这些情况要重建或部分重建 KV。"},
        ],
        "code": {
            "lang": "python",
            "caption": "带 KV Cache 的解码步骤（GQA 展开）",
            "content": r'''import torch
import torch.nn.functional as F

class KVCache:
    """每层独立的 K/V 缓存：形状 (B, n_kv_heads, T, d_head)"""
    def __init__(self, layers):
        self.k = [None] * layers
        self.v = [None] * layers

def gqa_step(q, k, v, n_heads, cache, layer):
    # q: (B, n_heads, 1, d) 本步新 token 的查询投影
    # k, v: (B, n_kv, 1, d) 本步新 token 的 KV 投影（GQA 下 n_kv < n_heads）
    if cache.k[layer] is None:
        cache.k[layer], cache.v[layer] = k, v
    else:
        cache.k[layer] = torch.cat([cache.k[layer], k], dim=2)  # 追加
        cache.v[layer] = torch.cat([cache.v[layer], v], dim=2)
    K, V = cache.k[layer], cache.v[layer]
    rep = n_heads // K.shape[1]          # GQA: KV 组复制到查询头数
    K = K.repeat_interleave(rep, dim=1)
    V = V.repeat_interleave(rep, dim=1)
    return F.scaled_dot_product_attention(q, K, V)   # 单 query 无需 mask

@torch.no_grad()
def generate(step_fn, prompt_ids, max_new=32, eos=None):
    cache, cur = KVCache(step_fn.layers), prompt_ids
    logits, cache = step_fn.prefill(cur, cache)      # 阶段1: 一次算整段
    out = []
    for _ in range(max_new):
        nxt = logits[:, -1].argmax(-1, keepdim=True)
        out.append(nxt)
        if eos is not None and nxt.item() == eos:
            break
        logits, cache = step_fn.decode(nxt, cache)   # 阶段2: 每步 1 token
    return torch.cat(out, dim=1)
# 说明: prefill 一次前向写满 cache；decode 每步只算新 token 的投影并追加,
# 注意力从 O(T^2) 降为 O(T)。生产实现用预分配缓冲替代逐层 cat。''',
        },
    },
    {
        "id": "transformer-036",
        "topic": "KVCache与推理优化",
        "type": "八股",
        "difficulty": 4,
        "frequency": 4,
        "companies": ["字节", "阿里", "华为", "NVIDIA"],
        "years": ["2024", "2025"],
        "question": "GPTQ 和 AWQ 这两种 INT4 权重量化有什么区别？各自的思想和适用场景是什么？",
        "answerMd": r'''**一句话核心**：两者都是训练后权重量化（W4A16），GPTQ 走「逐层重建误差最小化」——按 Hessian 信息量化一列、立刻补偿其对未量化列的误差；AWQ 走「激活感知缩放」——少数通道承担大部分激活能量，用等效缩放保护它们，不需要反向传播。

**1. GPTQ。** 把 OBQ（最优脑量化）近似到逐层：目标 $\min \|WX - \hat W X\|^2$，用该层输入的二阶信息 $H = 2XX^\top$ 指导顺序：每次量化一列权重，把引入的误差按 Hessian 逆权重的比例「摊」给尚未量化的列（误差补偿），循环推进。支持分组量化（group size 128 常见）、可结合 act-order 重排。优点是重建误差小、压缩比高；缺点是校准依赖、对分布漂移敏感，且逐列补偿的内核对硬件不友好（有融合改进）。

**2. AWQ。** 观察：约 0.1%~1% 的「显著」权重通道对应激活幅度特别大，对量化误差最敏感。它不直接混合精度，而是做数学等价变换：$y = (W \cdot \mathrm{diag}(s))(\mathrm{diag}(s)^{-1} x)$，搜索每通道缩放 $s$ 让显著通道的权重相对幅度变大、量化误差减小，激活侧用 SmoothQuant 类的动量对冲。无需反向传播、校准样本少，跨域泛化更好，内核友好。

**3. 选型与补充。** 一般建议：追求最低比特与最大压缩用 GPTQ，追求跨域稳健与速度用 AWQ（或两者混用）；相关还有 ZeroQuant/LLM.int8/SmoothQuant（W8A8）、KV fp8 量化。评估量化要同时看困惑度、下游任务与长上下文，长文本上 KV 量化的影响常大于权重量化。''',
        "keyPoints": [
            "GPTQ：Hessian 驱动的逐列量化 + 误差补偿，重建误差小",
            "AWQ：激活感知的通道缩放，保护显著通道，免反向传播",
            "两者都是 W4A16 权重量化，激活与 KV 默认仍高精度",
            "GPTQ 校准敏感、AWQ 跨域稳健、内核友好",
            "评估要看困惑度+下游+长上下文，勿只看 PPL",
        ],
        "followUps": [
            {"q": "为什么权重 4bit 而激活不量化？", "a": "激活有离群值且逐 token 动态变化，量化需要运行时统计与反量化开销，误差也更直接地进入计算；权重静态可离线校准。W4A16 让矩阵乘在反量化后走高精度路径，兼顾显存与数值安全。"},
        ],
    },
    # ---------------------------------------------------------------- MoE
    {
        "id": "transformer-037",
        "topic": "MoE",
        "type": "八股",
        "difficulty": 3,
        "frequency": 5,
        "companies": ["DeepSeek", "字节", "阿里", "月之暗面"],
        "years": ["2024", "2025"],
        "question": "MoE 的基本结构和工作流程是怎样的？为什么稀疏激活能「参数变大、算力不变」？",
        "answerMd": r'''**一句话核心**：MoE 把 Transformer 的 FFN 层换成「路由器 + N 个专家 FFN」，每个 token 只激活 top-k 个专家——总参数随专家数线性增长，单 token 计算量只随 k 增长，从而以近恒定算力扩容量；2025~2026 的开源旗舰基本都是 MoE。

**1. 工作流程。** 路由器是一个线性层 + softmax，给出 token 对每个专家的偏好分数；取 top-k（常 k=1~8）个专家，用其 softmax 概率加权各专家输出后求和；专家本身通常是缩小的 SwiGLU FFN。训练时对所有被激活的参数照常反传，路由分数靠可微的 top-k + 辅助损失学习。

**2. 为什么算力不变。** 密集模型每个 token 过全部 FFN 参数；MoE 中每 token 只过 k 个专家，FLOPs 正比于 $\sum$ 被激活参数。例如总参万亿、激活百亿级的配置（DeepSeek V3 671B/37B、Kimi K2 万亿/32B 量级），单 token 计算与几十 B 稠密模型相当，但「知识存储容量」是所有专家之和——这正是容量与算力解耦的逻辑。

**3. 代价与难点。** 一是负载不均：路由会自增强地集中到少数专家，需要辅助损失或 bias 调节；二是显存：全部专家要驻留 GPU，靠专家并行 + all-to-all 分摊；三是训练不稳与超参敏感（k、专家粒度、aux 系数）；四是推理系统复杂（专家并行、动态 batch、通信）。

**4. 演进方向。** 细粒度专家 + 共享专家（DeepSeekMoE）、更高稀疏度（激活率降到 3% 量级）、auxiliary-loss-free 负载均衡，以及把 MoE 与混合注意力层叠加（2026 年的典型旗舰配方）。''',
        "keyPoints": [
            "FFN → 路由器 + N 专家，每 token 激活 top-k 个",
            "参数随专家数增长、FLOPs 只随 k 增长，容量与算力解耦",
            "负载不均要 aux loss 或 bias 调节，否则路由塌缩",
            "全部专家驻显存，依赖专家并行与 all-to-all 通信",
            "2026 旗舰配方：细粒度+共享专家、超高稀疏度、混合注意力",
        ],
        "followUps": [
            {"q": "MoE 和 dense 比，同样激活参数下谁更强？", "a": "公开对比普遍认为同激活算力下 MoE 的 loss 与下游更好，因为总容量大；但 MoE 训练更难调、显存占用高、推理系统复杂。小模型或数据受限时，dense 可能更划算。"},
        ],
    },
    {
        "id": "transformer-038",
        "topic": "MoE",
        "type": "手撕",
        "difficulty": 4,
        "frequency": 4,
        "companies": ["DeepSeek", "字节", "智谱"],
        "years": ["2024", "2025"],
        "question": "写一下 MoE 的负载均衡辅助损失（Switch 式），并解释 DeepSeek V3 的 auxiliary-loss-free 方案为什么更好。",
        "answerMd": r'''**一句话核心**：Switch 式辅助损失 $L_{aux} = \alpha N \sum_i f_i P_i$ 用「实际负载比例 f × 平均路由概率 P」衡量不均衡，均匀时取最小；DeepSeek V3 改为只对路由分数加一个按负载自动升降的 per-expert bias——不干扰梯度、不强迫均匀，负载均衡效果相当且质量更好。

**1. 公式与直觉。** $f_i$：一个 batch 里分给专家 i 的 token 比例；$P_i$：路由器给专家 i 的平均概率。两者同时大才说明「既想给又真给了」，乘积求和在不均匀时增大；乘 $N$ 是为了把「完全均匀」归一到常数 1。问题：它是加在主损失上的强正则——为了均衡会牺牲路由质量（该集中的不让集中），系数难调，且与 LM 目标相互干扰。

**2. auxiliary-loss-free（DeepSeek V3）。** 给每个专家维护一个偏置 $b_i$，只加在路由打分（top-k 选择）上、不进加权的门控值；每步结束后统计负载：过载专家 $b_i \leftarrow b_i - \gamma$，欠载 $b_i \leftarrow b_i + \gamma$（$\gamma$ 是小步长超参）。这样均衡成了「打分的负反馈调节器」，主梯度完全不掺均衡项，专家还能按语义自然分化。

**3. 实现要点。** 代码里注意：bias 要 detach（不参与反传）；$f_i$ 用 argmax/top-k 的硬计数、$P_i$ 用 softmax 概率；均匀时 $(f_i = 1/N, P_i = 1/N)$ 损失恰为 $\alpha$。可另配 router z-loss 防分数爆炸。''',
        "keyPoints": [
            "L_aux = alpha * N * sum(f_i * P_i)，均匀时最小",
            "f_i 是硬负载比例，P_i 是软路由概率",
            "aux loss 与主目标相互干扰，系数敏感",
            "aux-free：bias 只改路由打分，按负载升降不进梯度",
            "可叠加 z-loss 抑制路由分数爆炸",
        ],
        "followUps": [
            {"q": "为什么 bias 不能加进门控权重里？", "a": "门控权重决定专家输出的混合系数，影响梯度方向；若 bias 参与加权，均衡信号会直接改变前向输出并引入额外梯度，等价于又造了一个 aux loss。只作用于 top-k 选择则纯粹是「谁被选中」的调度偏置。"},
        ],
        "code": {
            "lang": "python",
            "caption": "Switch 式负载均衡辅助损失 + aux-free bias 更新",
            "content": r'''import torch

def switch_aux_loss(routing_probs, expert_ids, n_expert, alpha=1e-2):
    """routing_probs: (T, E) softmax 概率; expert_ids: (T,) 实际选中的专家"""
    T = routing_probs.shape[0]
    one_hot = torch.zeros_like(routing_probs).scatter_(
        1, expert_ids.unsqueeze(1), 1.0)
    f = one_hot.mean(0)                      # 每 expert 实际负载比例
    P = routing_probs.mean(0)                # 每 expert 平均路由概率
    return alpha * n_expert * (f * P).sum()  # 完全均匀时 = alpha

@torch.no_grad()
def update_bias(expert_load, bias, capacity, gamma=1e-3):
    """auxiliary-loss-free: 按负载升降路由 bias（不参与反传）"""
    overload = expert_load > capacity        # 每 expert 承接数 vs 容量
    bias[overload] -= gamma                  # 过载降分
    bias[~overload] += gamma                 # 欠载升分
    return bias

probs = torch.softmax(torch.randn(64, 8), dim=-1)   # 8 个专家
ids = probs.argmax(-1)
print(switch_aux_loss(probs, ids, 8).item())        # 越不均衡越大''',
        },
    },
    {
        "id": "transformer-039",
        "topic": "MoE",
        "type": "八股",
        "difficulty": 4,
        "frequency": 4,
        "companies": ["DeepSeek", "月之暗面", "MiniMax"],
        "years": ["2024", "2025"],
        "question": "DeepSeekMoE 的「细粒度专家 + 共享专家」设计解决了什么问题？跟 Mixtral 那种大专家有什么不同？",
        "answerMd": r'''**一句话核心**：细粒度专家把大专家切成更多小专家、每 token 激活更多个，让「专家组合」的组合爆炸式增加、知识拆分更细；共享专家每个 token 必过，负责承接通用共性知识，从而减少路由专家间的知识冗余——两者合起来提升同激活算力下的参数效率。

**1. 细粒度分割。** Mixtral 式是少量大专家（如 8 选 2，每个是完整尺寸 FFN）：组合数 $\binom{8}{2}=28$ 种，每个专家内部要同时装多种知识，冗余高。DeepSeekMoE 把专家切细（如 64 个小专家选 6 个），组合数升到数百万量级，路由可以为每种「知识组合」挑不同的专家子集，专家分工更专、更可解释；同时每个专家更小，激活总数可控。

**2. 共享专家。** 各 token 不论路由到谁，都要过 1 个（或少数几个）共享专家：高频通用能力（语法、常识、常见变换）沉淀在这里，路由专家就不必各自学一遍，减少了专家之间的重复参数。DeepSeek V3 的配置是 1 个共享专家加 256 个细粒度路由专家、每 token 激活 8 个路由专家（另加 1 个 MTP 预测模块，属于推理加速部分）。

**3. 效果与权衡。** 同激活 FLOPs 下 DeepSeekMoE 式配置在公开对比中质量更优，被 DeepSeek V3、Qwen3-MoE、Kimi 系等跟进（各家专家数与激活数不同）。权衡：专家数多则 all-to-all 路由更碎、对通信与负载均衡更敏感；共享专家是常驻计算，设计上不能太大。''',
        "keyPoints": [
            "细粒度专家：更多更小的专家，组合空间指数扩大",
            "共享专家：每 token 必过，沉淀通用知识减少冗余",
            "DeepSeek V3：1 共享 + 256 路由专家，激活 8 个",
            "同激活算力下参数效率优于少量大专家（Mixtral 式）",
            "代价：路由更碎，对 all-to-all 与负载均衡更敏感",
        ],
        "followUps": [
            {"q": "共享专家和第一个专家常被选中是一回事吗？", "a": "不是。共享专家是结构上强制激活、不经路由，输出以固定权重加入；路由专家仍按分数竞争。前者保证通用计算路径恒定，后者负责按内容 specialization，两者互补。"},
        ],
    },
    {
        "id": "transformer-040",
        "topic": "MoE",
        "type": "八股",
        "difficulty": 4,
        "frequency": 3,
        "companies": ["字节", "华为", "NVIDIA"],
        "years": ["2024", "2025"],
        "question": "MoE 里的容量因子（capacity factor）是干什么的？专家并行下 all-to-all 通信怎么优化？",
        "answerMd": r'''**一句话核心**：容量因子 CF 决定每个专家最多承接多少 token（$\text{capacity} = \frac{\text{batch token 数}}{\text{专家数}} \times CF$）：CF 太小丢 token、太大 padding 浪费算力；专家并行把专家散到不同 GPU，token 出入要经 all-to-all，优化靠通信-计算重叠、拓扑感知排布与细粒度调度。

**1. 容量因子。** 路由是动态的，热门专家可能被分到远超均值的 token。标准做法设硬容量：超出的 token「溢出」，其 FFN 输出用残差直通或零代替（token dropping）。CF=1.0 时均值即上限，丢 token 多；CF=1.25~2.0 是常见区间，代价是冷门专家的槽位空转（padding）。训练一般用较高 CF 保证质量，推理可降 CF 换吞吐；Dropless MoE（如 MegaBlocks 用稀疏内核）则不做硬容量，按需计算。

**2. 专家并行与 all-to-all。** token 先在卡内算出路由，再把每个 token 发送到其专家所在的卡（dispatch），算完再发回（combine），两次 all-to-all。优化点：一是把 all-to-all 与注意力/共享计算重叠（异步流水）；二是专家放置与数据分布匹配（热点专家复制副本）；三是分组 all-to-all 利用 NVLink 域内高带宽、跨机走 IB 并压缩；四是与 EP/TP/DP 组合成多维并行时，让专家维度吃 EP、把 DP 副本做数据分摊；五是 MoE 层与稠密层配比影响通信占比，序列打包也能摊薄固定开销。''',
        "keyPoints": [
            "capacity = 每 batch 均摊 token 数 × CF",
            "CF 小则 token 溢出丢失，大则 padding 浪费，常见 1.25~2.0",
            "dropless 方案用稀疏内核免硬容量",
            "EP 下 dispatch/combine 两次 all-to-all 是主要通信",
            "优化：重叠通信、热点专家复制、域内高带宽分组、多维并行",
        ],
        "followUps": [
            {"q": "推理时容量因子怎么选？", "a": "推理丢 token 会直接伤输出质量，一般取保守 CF 或用 dropless；在显存吃紧时才允许溢出并配合降级策略。也可以按负载动态调整 batch 组成，让每步路由更均衡。"},
        ],
    },
    {
        "id": "transformer-041",
        "topic": "MoE",
        "type": "场景",
        "difficulty": 4,
        "frequency": 3,
        "companies": ["字节", "DeepSeek", "阿里"],
        "years": ["2024", "2025"],
        "question": "训练 MoE 时发现 loss 正常下降但专家负载越来越集中（熵塌缩），你会怎么排查和处理？",
        "answerMd": r'''**一句话核心**：先确认是「路由塌缩」还是「数据天然不均」——看专家负载曲线、路由熵与被丢弃 token 比例；处理上按优先级调 aux/bias 均衡强度、检查路由实现细节（fp32 路由、初始化、bias 是否进梯度），再考虑专家数与 k 的结构改动。

**1. 排查顺序。** 监控三件套：每专家负载直方图（是否出现长尾 hot/cold）、每步路由熵（塌缩则单调下降到近 0）、溢出 token 率（CF 内丢了多少）。若个别专家负载 >80% 而大量专家接近 0，是典型塌缩；若分布只是轻度倾斜且下游指标正常，可能是数据域导致的合理分工，不必强改。

**2. 常见根因。** 一是均衡信号太弱或失效：aux 系数过小、bias 更新被写进了计算图（应 detach）、top-k 用了错误的打分（忘了加 bias）；二是数值问题：路由用 bf16 导致分数误差被放大，应 fp32 算 softmax；三是初始化/学习率：router 权重初始过大、lr 过高导致早期一次大梯度锁死；四是数据问题：某类数据爆发式重复，token 全涌向某一专家。

**3. 处理手段（由轻到重）。** 调大 aux 系数或切换 aux-free bias 均衡（推荐，DeepSeek V3 式）；加 router z-loss 稳分数；路由层独立学习率；重启时把塌缩的 router 恢复到早Checkpoint；结构上减少专家数或增大 k、把专家粒度调细以增加组合自由度。处理后要持续观察：健康状态是负载大体均匀但非强制均匀、熵缓降不坍塌、溢出率低。''',
        "keyPoints": [
            "先区分路由塌缩与数据驱动的合理不均",
            "监控：负载直方图、路由熵、溢出 token 率",
            "检查 bias 是否 detach、路由是否 fp32、aux 系数与 z-loss",
            "推荐 aux-free bias 均衡 + router 独立学习率",
            "重度时改结构：专家数/k/粒度，或回滚 router 权重",
        ],
        "followUps": [
            {"q": "为什么 MoE 训练比 dense 更容易 loss spike？", "a": "路由是离散 top-k，分数的小抖动可能造成 token 大规模换专家，梯度方向突变；叠加 all-to-all 数值与负载突变的耦合，容易出现 spike。常见缓解是 fp32 路由、z-loss、aux-free bias 平滑调节与更小的路由学习率。"},
        ],
    },
    # ---------------------------------------------------------------- 显存与计算量估算
    {
        "id": "transformer-042",
        "topic": "显存与计算量估算",
        "type": "八股",
        "difficulty": 4,
        "frequency": 5,
        "companies": ["字节", "阿里", "华为", "快手"],
        "years": ["2024", "2025"],
        "question": "用混合精度 AdamW 训练一个 7B 模型，显存都花在哪了？为什么说单张 80G 卡装不下，8 张卡才够？",
        "answerMd": r'''**一句话核心**：混合精度 AdamW 下每参数约 16 字节（fp16 权重 2 + fp16 梯度 2 + fp32 主权重 4 + 一二阶动量各 4），7B 即约 112GB，还没算激活——单卡 80G 放不下，8 卡用 ZeRO/FSDP 把状态分片后每人约 14GB，再加激活才可行。

**1. 状态显存明细（每参数字节）。** fp16 参数 2B；fp16 梯度 2B；混合精度为保数值稳定保留 fp32 主权重 4B（优化器实际更新它）；Adam 一阶动量 m 4B、二阶动量 v 4B（fp32）。合计 16B/参数 → 7B × 16 = 112GB。有些实现还会多存 fp32 梯度备份或用 bf16 省主权重，量级在 112~128GB。

**2. 激活显存。** 与 batch×seq、层数、宽度成正比：开 full activation checkpointing 时只存每层入口隐状态，约 $2 \times L \times b \times s \times d \times 2$ 字节（fp16 存输入+反向重算），如 $b \cdot s = 16384$、$d = 4096$、$L = 32$ 约为 8.6GB；不开重计算则要存每层中间激活（GELU 输入、注意力 logits 等），翻好几倍。FlashAttention 免掉注意力矩阵存储是长序列的前提。

**3. 怎么塞下。** 8 卡方案：ZeRO-2（切优化器状态+梯度）每人约 26GB（fp16 参数 14GB 整份驻卡 + 分摊的状态与梯度约 12GB）+ 激活即可单机跑；ZeRO-3/FSDP 再切参数，可上更大 batch 或更长序列；再加梯度累积凑大 batch。若 8 卡还想省，可上 bf16（免 loss scale，不动主权重结构）、8bit 优化器（状态减半）等。结论要能脱口而出：**7B 训练的参数态显存 ≈ 16×7 ≈ 112GB，激活另算**，这就是「8×80G 才舒服」的来源。''',
        "keyPoints": [
            "16B/参数：fp16 权重+梯度 4B、fp32 主权重 4B、动量 8B",
            "7B → 112GB 参数态，80G 单卡放不下",
            "激活随 b*s*L*d 增长，重计算+FlashAttention 是标配",
            "ZeRO-2 切状态+梯度即单机 8 卡可跑 7B",
            "bf16 免 loss scale；8bit 优化器可再省动量",
        ],
        "followUps": [
            {"q": "为什么 Adam 动量必须存 fp32？", "a": "m/v 是跨步累积量，会累加大量小梯度；fp16 只有 11 位尾数，累加误差和下溢会破坏二阶矩估计，进而让自适应步长失真。fp32 主权重同理：fp16 参数更新步长可能小于可表示精度而丢失。"},
        ],
    },
    {
        "id": "transformer-043",
        "topic": "显存与计算量估算",
        "type": "八股",
        "difficulty": 4,
        "frequency": 4,
        "companies": ["字节", "面壁智能", "智谱", "OpenAI"],
        "years": ["2024", "2025"],
        "question": "推导一下训练 FLOPs 的 6ND 公式，并用它算：7B 模型训 1T token 需要多少计算量？Chinchilla 最优数据量是多少？",
        "answerMd": r'''**一句话核心**：每个 token 的前向约 $2N$ FLOPs（每个权重一次乘加）、反向约为其两倍 $4N$，合计 $6ND$；7B×1T = $4.2 \times 10^{22}$ FLOPs，按 Chinchilla 最优配比 7B 应配约 140B token，1T 已是 7 倍过训练。

**1. 推导。** 矩阵乘 $y = Wx$（$W$ 是 $m \times n$）对每个输入向量需 $2mn$ FLOPs（乘加各一）。Transformer 前向每个 token 大约把每个参数用到一次线性变换（注意力投影 + FFN），即 $\approx 2N$ FLOPs/token（$N$ 为参数量；attention 的 $n^2$ 项在通常长度下可忽略）。反向传播要算「对输入的梯度」与「对权重的梯度」，各相当于一次前向量级的矩阵乘，故反向 $\approx 4N$。总训练计算 $C \approx 6ND$，推理（只前向）$2ND$。

**2. 算例。** $N = 7 \times 10^9$，$D = 10^{12}$：$C = 6 \times 7 \times 10^9 \times 10^{12} = 4.2 \times 10^{22}$ FLOPs。换算时间：单张 A800/A100 的 BF16 稠密算力约 312 TFLOPS，MFU 取 40% → 有效 $1.25 \times 10^{14}$ FLOP/s → 约 $10.7$ 年单卡；512 卡有效 $6.4 \times 10^{16}$ → 约 7.6 天。这套换算要能现场口算。

**3. Chinchilla 关联。** 计算最优训练满足 $D \approx 20N$（tokens per param），7B 对应约 140B token；同算力下「更小模型 + 更多 token」优于 GPT-3 式配比。而 Llama 3 405B 训 15T+ token（远超 20N）属于推理 aware 的过训练：牺牲训练侧最优换取推理侧更小的模型达到同等质量。''',
        "keyPoints": [
            "前向 2N、反向 4N，总 6ND FLOPs；推理 2ND",
            "7B × 1T = 4.2e22 FLOPs，可按 MFU 折算卡时",
            "Chinchilla：D ≈ 20N 计算最优，7B ≈ 140B token",
            "前沿模型普遍 5~100 倍过训练，为推理成本优化",
            "attention 的 n^2 项在超长上下文时要另加",
        ],
        "followUps": [
            {"q": "为什么反向是前向的两倍？", "a": "反向要算两类梯度：激活梯度（把上游梯度乘回权重）与权重梯度（激活外积），两者各是一次与该层等规模的矩阵乘，加起来约为一次前向的两倍，工程实测 6ND 与实际功耗吻合良好。"},
        ],
    },
    {
        "id": "transformer-044",
        "topic": "显存与计算量估算",
        "type": "场景",
        "difficulty": 4,
        "frequency": 3,
        "companies": ["字节", "阿里", "美团"],
        "years": ["2024", "2025"],
        "question": "线上要部署一个 7B（GQA 8 KV 头）fp16 模型到单张 A800 80G，估算最多能撑多少并发、单流解码速度的量级，瓶颈在哪？",
        "answerMd": r'''**一句话核心**：权重 14GB 剩约 66GB 给 KV；128KB/token 的 KV 下 4K 上下文每条约 0.5GB，理论并发可上百，但实际受延迟 SLO 与调度限制；单流 decode 是带宽瓶颈，量级约百 token/s。

**1. 显存账。** fp16 权重 $7 \times 2 = 14$GB（再留激活/框架开销约 2~4GB）。KV：$2 \times 32 \text{层} \times 8 \text{头} \times 128 \text{维} \times 2\text{B} = 128$KB/token。4K 上下文 → 0.5GB/条，66GB 可容纳约 130 条；8K 则减半。若开 PagedAttention 碎片极小，这账基本能兑现；如果用 MHA 版本（512KB/token）则只有约 32 条。

**2. 速度账。** decode 每生成一个 token 要把 14GB 权重整个读一遍（batch=1 时），A800 显存带宽约 2TB/s → 上限约 $2000/14 \approx 140$ token/s，考虑内核效率打 5~7 折，单流量级 70~100 token/s。batch=N 时权重读取被 N 条请求分摊，总吞吐可继续涨，直到 KV 读取成为新瓶颈（上下文越长越早到顶）。

**3. 瓶颈与对策。** 结论：单流慢是因为 memory-bound，不是算力不够；并发上限受 KV 显存约束。提升手段按性价比：GQA 已用 → 上 KV fp8 量化（KV 减半，并发翻倍）、prefix caching（公共系统提示只存一份）、continuous batching 打满带宽、投机解码降单流延迟；若上下文业务要求 32K+，考虑 MLA 结构或稀疏注意力模型。答题时给出「显存账 + 带宽账」两个估算就足够展示功底。''',
        "keyPoints": [
            "权重 14GB，KV 128KB/token（GQA 8 头 fp16）",
            "4K 上下文 0.5GB/条 → 80G 卡理论并发上百",
            "单流 decode 上限 ≈ 带宽/权重体积 ≈ 140 tok/s，实际打折",
            "batch 推高吞吐直到 KV 带宽接棒成为瓶颈",
            "提速顺序：KV 量化 > prefix caching > 投机解码",
        ],
        "followUps": [
            {"q": "为什么 batch 增大后吞吐不再线性涨？", "a": "batch 小时每步读权重是固定开销，吞吐随 batch 线性涨；batch 大后每步要读的 KV 总量随并发增长，KV 带宽取代权重成为瓶颈，吞吐增速放缓，同时延迟上升，需要在 SLO 下取平衡点。"},
        ],
    },
    # ---------------------------------------------------------------- 结构前沿
    {
        "id": "transformer-045",
        "topic": "结构前沿",
        "type": "八股",
        "difficulty": 4,
        "frequency": 4,
        "companies": ["DeepSeek", "阿里", "月之暗面", "智谱"],
        "years": ["2025", "2026"],
        "question": "以 2025~2026 的主流开源模型为例，比较一下 Llama、Qwen、DeepSeek、GLM、Kimi 在结构选型上的异同。",
        "answerMd": r'''**一句话核心**：共同底座高度一致（Pre-RMSNorm + SwiGLU + RoPE + 因果注意力），分歧集中在三处：注意力取 GQA/MLA/混合线性、FFN 取 dense 还是 MoE、以及长上下文与推理效率的配套设计；趋势是 MoE 化 + 注意力混合化。

**1. 共同底座。** decoder-only、Pre-RMSNorm（带 final norm）、SwiGLU FFN、RoPE、无 dropout 的预训练范式；这些已是行业公约数，面试先说这个再说差异。

**2. 注意力与 FFN 分歧。** Llama 系（1~3）是 GQA 稠密的标杆，Llama 4 转向 MoE 并引入 iRoPE（部分层无位置编码/交错全局局部）拉长上下文；Qwen 系 dense 与 MoE 并行（如 235B-A22B 级 MoE），用 QK-Norm 替代 QKV bias 稳训练，Qwen3-Next 进一步走混合线性注意力 + 超高稀疏 MoE；DeepSeek V3 是 MLA + 细粒度共享专家 MoE + MTP + FP8 训练的代表，V3.2 起引入稀疏注意力降长上下文成本；GLM-4.5 级为 355B/A32B 档 MoE；Kimi K2 为万亿总参/百亿级激活的 MoE（沿用 MLA 类设计，训练上报告了 Muon 类优化器与注意力熵控制手段）。Gemma 3 用 5:1 局部/全局交错注意力 + QK-Norm，GPT-OSS 用滑动窗交替 + 注意力 sink + MXFP4 原生量化。具体数字以各家技术报告为准，面试重点讲「选型逻辑」而非背参数。

**3. 选型逻辑。** dense vs MoE：算力预算大、追求容量 → MoE；小尺寸部署 → dense。注意力：生态兼容 GQA、极致 KV 压缩 MLA、长上下文降本稀疏/混合线性。多模态统一用 ViT 编码 + 投影接入或原生早期融合。''',
        "keyPoints": [
            "公约数：Pre-RMSNorm + SwiGLU + RoPE + decoder-only",
            "注意力三派：GQA（生态）/ MLA（KV 压缩）/ 混合线性（长上下文）",
            "FFN：Llama4 后稠密转 MoE 成为旗舰标配，稀疏度不断提高",
            "配套创新：QK-Norm、MTP、FP8 训练、稀疏注意力",
            "具体参数以技术报告为准，重点讲选型逻辑",
        ],
        "followUps": [
            {"q": "如果让你设计一个 2026 年的新模型底座，你会怎么选？", "a": "万亿级总参 MoE（细粒度+共享专家，激活 3% 量级）+ 混合注意力（3:1 线性:全注意力或稀疏注意力）+ MLA 式 KV 压缩 + MTP 头 + FP8 训练，长上下文原生到 128K 起步；这是当前公开配方中性价比最高的一档。"},
        ],
    },
    {
        "id": "transformer-046",
        "topic": "结构前沿",
        "type": "八股",
        "difficulty": 4,
        "frequency": 3,
        "companies": ["阿里", "月之暗面", "MiniMax", "DeepSeek"],
        "years": ["2025", "2026"],
        "question": "「混合注意力层」（大部分层线性注意力 + 少量层全注意力）为什么在 2025~2026 成为潮流？比例怎么定？",
        "answerMd": r'''**一句话核心**：decode 的成本大头是「读 KV」，线性注意力层把历史压进固定状态、几乎免 KV 读取，但精确召回弱；混合架构用 3:1 到 7:1 的比例让少数全注意力层负责精确记忆，实测少量全注意力就能保住检索能力，于是长上下文与推理成本同时受益，成为 Qwen3-Next、Kimi Linear、MiniMax 等的共同选择。

**1. 动机。** 纯 Transformer 的推理成本随上下文线性膨胀（KV 带宽），纯线性/SSM 又在检索、复制类任务上明显掉分。实测发现「每 3~8 层放 1 层全注意力」就能恢复大部分远程检索能力——因为检索需要的是「高带宽旁路」，不需要每层都全局。Qwen3-Next 用 Gated DeltaNet 与门控注意力约 3:1 交错；Kimi Linear 用 KDA 与 MLA 约 3:1（论文报告 KV 缓存减少约 75%、解码加速数倍）；更早的 MiniMax-01（lightning attention 约 7:1）、Jamba（Mamba:注意力约 7:1）验证了更激进的比例也可行。

**2. 设计要点。** 一是线性层的选择：Gated DeltaNet/KDA 这类「误差修正写状态」的递推比朴素线性注意力记忆质量高；二是全注意力层的位置与数量是关键超参，通常均匀交错；三是训练侧要配长上下文数据与 MTP 等，弥补线性层的表达能力差；四是推理引擎需要专门内核（chunked 并行 scan）才能兑现理论收益。

**3. 趋势判断。** 2026 年这已是旗舰配方的一部分：DeepSeek 据公开报道在 V4 转向混合注意力（压缩稀疏 + 重压缩全局）支撑百万级上下文；社区共识是「线性层管效率、全注意力管记忆」，下一战场是长上下文精确召回质量。''',
        "keyPoints": [
            "decode 瓶颈是 KV 带宽，线性层用固定状态免 KV 读取",
            "少量全注意力层即可恢复远程检索能力",
            "公开配方比例 3:1（Qwen3-Next/Kimi Linear）到 7:1（MiniMax/Jamba）",
            "线性层选型偏向 DeltaNet/KDA 类误差修正递推",
            "需要专门内核（并行 scan）与长上下文训练配合",
        ],
        "followUps": [
            {"q": "混合架构的短板是什么？", "a": "一是训练工程复杂，两套算子与并行策略要兼容；二是 KV/状态在层间不一致，前缀缓存和投机解码的适配要重做；三是超长距离精确检索仍弱于全注意力，需要靠全注意力层数与稀疏注意力补。"},
        ],
    },
    {
        "id": "transformer-047",
        "topic": "结构前沿",
        "type": "八股",
        "difficulty": 3,
        "frequency": 4,
        "companies": ["阿里", "字节", "OpenAI", "Google"],
        "years": ["2024", "2025", "2026"],
        "question": "多模态能力是怎么接进 LLM 的？对比「编码器 + 投影」与「原生早期融合」两条路线。",
        "answerMd": r'''**一句话核心**：主流是「视觉/音频编码器 + 投影层把特征当外语 token 喂给 LLM」，改动小、成熟快；原生早期融合则把各模态 token 混进同一个 Transformer 从预训练就一起学，上限更高但训练贵且不稳；2025~2026 的全模态模型多为两条路线的折中。

**1. 编码器 + 投影（adapter 路线）。** ViT（如 CLIP/SigLIP 系列）把图像切成 patch 编码，经 MLP projector（LLaVA 式）或 resampler/交叉注意力（Flamingo/Qwen-VL 式）映射到 LLM 词表空间，与文本 token 一起过 decoder；LLM 主体可冻结或继续训练。优点：复用成熟视觉编码器与预训练 LLM、数据效率高、分期训练可控；缺点：分辨率受 patch 方案限制（OCR 需动态分辨率/切片）、模态间深层交互有限、多编码器架构碎片化。

**2. 原生早期融合。** 所有模态（文本、图、音、视频）统一 tokenizer 化，放进同一个大 Transformer 做统一的 next-token 预测（Chameleon、GPT-4o 类的全模态方向）：模态间从底层就共享表征，能做交错生成（边看边说）、理解生成一体；代价是需要海量对齐数据、训练稳定性差（模态梯度冲突、loss 尺度不一）、算力成本高，通常要在数据配比和 loss 加权上精细调。

**3. 工程细节与趋势。** 高分辨率图像用动态分辨率切 patch + 位置编码插值；语音流式接入用分块编码；视频抽帧 + 时序位置编码。2026 年趋势是「原生融合为主干 + 专用编码器做外挂」的混合式，以及 any-to-any（图文音视频互生成）统一模型；面试时强调两条路线的 trade-off 与「训练成本-能力上限」的权衡即可。''',
        "keyPoints": [
            "adapter 路线：ViT 编码 + projector 映射为外语 token",
            "早期融合：全模态统一 tokenizer + 单一 Transformer",
            "adapter 成熟低成本，早期融合上限高、训练贵且不稳",
            "高分辨率靠动态 patch 与位置编码扩展",
            "趋势：混合式（原生主干 + 专用编码器）与 any-to-any",
        ],
        "followUps": [
            {"q": "为什么 OCR 类任务对多模态结构特别敏感？", "a": "OCR 需要细粒度文字还原，低分辨率 patch 或粗投影会丢字形细节；需要动态分辨率（按长宽比切块）、高压缩比 projector 或直接用像素 patch 进 LLM，这也是各模型在文档理解上拉开差距的地方。"},
        ],
    },
]

# -*- coding: utf-8 -*-
# 项目实战深挖 · 第一批（纯数据文件，顶部不 import）
# 覆盖 5 个项目：MiniGPT 预训练 / FlashAttention / LoRA-QLoRA 微调 / GRPO / RM+PPO 对齐
# 每个项目 bodyMd 固定五段结构：背景与思路 / 架构设计 / 关键组件实现 / 深挖追问 / 面试加分点

PROJECTS = [
    # ================================================================ proj-001
    {
        "id": "proj-001",
        "name": "MiniGPT：从零实现并训练一个小型 GPT",
        "domain": "pretrain",
        "level": "经典",
        "tags": ["预训练", "PyTorch"],
        "summaryMd": r'''从零实现并训练一个约 1M 参数的小型 GPT：简版 BPE tokenizer、多头因果注意力、Pre-LN 残差块、训练循环与 top-p 采样全部手写在一个文件里。做完你会对预训练的每个设计选择形成肌肉记忆；面试时先讲 next-token 预测的数据流，再现场手撕因果 mask 与采样逻辑，最加分的是能解释小语料上的过拟合、memorization 与 loss spike 等实操现象。''',
        "bodyMd": r'''## 背景与思路

GPT 的全部能力都来自一个目标：给定前文 $x_{\le t}$，最大化 $\log p(x_{t+1}\mid x_{\le t})$，也就是 next-token 预测。本项目把这条链路完整走一遍——文本 → BPE 编码 → embedding → 多层 Transformer → logits → 交叉熵 → 采样生成，全部手写在一个文件里。单文件实现强迫你触碰每一个设计决策：为什么 softmax 前要除以 $\sqrt{d_{head}}$、为什么用 Pre-LN、为什么输出头与 embedding 共享权重、top-p 采样的 cutoff 到底怎么写。这些正是预训练面试的高频追问点，也是「训练小语料看现象」的最佳实验台。

上手顺序：先跑通前向（形状对、初始 loss 接近 $\ln V$），再跑训练（train loss 下降、val loss 出现 U 形），最后接采样（能生成通顺文本）。

## 架构设计

MiniGPT 配置：词表 512、d_model 128、4 层 4 头、block_size 256，约 1~2M 参数，CPU 可训。数据流分四段：

1. **Tokenizer**：byte-level BPE，把任意 Unicode 文本映射成整数序列，中文天然覆盖；
2. **模型**：token embedding + 可学习位置 embedding 相加 → 4 个「LN → 因果注意力 → 残差 → LN → MLP → 残差」块 → 最终 LN → 共享权重的输出头；
3. **训练**：随机窗口切 (x, y) 对（y 是 x 右移一位），交叉熵只在预测位置计 loss，AdamW + warmup + cosine + 梯度裁剪；
4. **生成**：temperature 软化分布 → top-p 截尾 → 多项式采样，逐 token 追加。

设计取舍对齐 GPT-2：Pre-LN 保证深网络梯度稳定；qkv 合成一个大矩阵减少算子开销；weight tying 省参数并给初始 loss 一个天然上界（$\ln V$）。

## 关键组件实现

### 1. 简版 BPE tokenizer

为什么从 tokenizer 开始：模型只认整数，词表决定序列长度、中文处理与 OOV 表现。选择 byte-level 而非 char-level，是因为中文无法枚举成字符表；以 UTF-8 字节为最小单位，任何文本都能无损编码。BPE 的直觉是压缩：每次合并语料中出现最多的相邻符号对，能让编码总长度减少最多；训练时记录合并顺序，encode 时按同一顺序回放，训练与推理才一致。

```python
from collections import Counter

class SimpleBPE:
    # byte-level BPE：统计相邻 token 对频次、贪心合并最高频对
    def __init__(self, vocab_size=512):
        self.vocab_size = vocab_size
        self.merges = {}                     # (a, b) -> 新 id，保序记录合并历史
    def _count_pairs(self, ids):
        counts = Counter()
        for a, b in zip(ids, ids[1:]):
            counts[(a, b)] += 1
        return counts
    def _apply_merge(self, ids, pair, new_id):
        # 一趟扫描把 pair 换成 new_id；从左到右贪心，不重复利用刚合并出的 token
        out = []
        i = 0
        while i < len(ids):
            if i + 1 < len(ids) and ids[i] == pair[0] and ids[i + 1] == pair[1]:
                out.append(new_id)
                i += 2
            else:
                out.append(ids[i])
                i += 1
        return out
    def train(self, text):
        # 以 UTF-8 字节为最小单位：任意语言（含中文）都能覆盖，没有 OOV
        ids = list(text.encode('utf-8'))
        self.bytes = {i: bytes([i]) for i in range(256)}
        for step in range(self.vocab_size - 256):
            counts = self._count_pairs(ids)
            if not counts:
                break
            top = max(counts, key=counts.get)      # 最高频对 = 压缩收益最大
            new_id = 256 + step
            ids = self._apply_merge(ids, top, new_id)
            self.merges[top] = new_id              # encode 时按同序回放
            self.bytes[new_id] = self.bytes[top[0]] + self.bytes[top[1]]
    def encode(self, text):
        ids = list(text.encode('utf-8'))
        for pair, new_id in self.merges.items():   # dict 保序，与训练一致
            ids = self._apply_merge(ids, pair, new_id)
        return ids
    def decode(self, ids):
        return b''.join(self.bytes[i] for i in ids).decode('utf-8', errors='replace')
```

### 2. 多头因果注意力与 Transformer 块

attention 里最容易写错、也最容易被追问的三行：qkv 的 view/transpose、除以 $\sqrt{d_{head}}$、因果 mask。缩放的理由是 $q\cdot k$ 是 $d_{head}$ 个内积之和，方差随维度线性增长，不缩放则 softmax 输入过大、输出趋近 one-hot、梯度消失。mask 用下三角矩阵对所有头广播，屏蔽未来 token——这正是「训练目标与自回归生成一致」在代码上的落点。

```python
import math
import torch
import torch.nn as nn
import torch.nn.functional as F

class CausalSelfAttention(nn.Module):
    def __init__(self, d_model, n_head, block_size, dropout=0.0):
        super().__init__()
        assert d_model % n_head == 0, 'd_model 必须能被 n_head 整除'
        self.n_head = n_head
        self.head_dim = d_model // n_head
        self.qkv = nn.Linear(d_model, 3 * d_model, bias=False)   # q/k/v 合成一个矩阵
        self.proj = nn.Linear(d_model, d_model, bias=False)      # 多头拼接后的输出投影
        self.attn_drop = nn.Dropout(dropout)
        self.resid_drop = nn.Dropout(dropout)
        # 因果 mask 只依赖长度，注册为 buffer 避免每步重算
        mask = torch.tril(torch.ones(block_size, block_size))
        self.register_buffer('mask', mask.view(1, 1, block_size, block_size))
    def forward(self, x):
        B, T, C = x.shape
        q, k, v = self.qkv(x).split(C, dim=2)                    # 各 (B, T, C)
        q = q.view(B, T, self.n_head, self.head_dim).transpose(1, 2)
        k = k.view(B, T, self.n_head, self.head_dim).transpose(1, 2)
        v = v.view(B, T, self.n_head, self.head_dim).transpose(1, 2)
        # 除以 sqrt(d_head)：q·k 的方差随维度线性增长，不缩放 softmax 会饱和
        att = (q @ k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        att = att.masked_fill(self.mask[:, :, :T, :T] == 0, float('-inf'))
        att = F.softmax(att, dim=-1)
        att = self.attn_drop(att)
        y = att @ v                                              # (B, n_head, T, head_dim)
        y = y.transpose(1, 2).contiguous().view(B, T, C)
        return self.resid_drop(self.proj(y))

class MLP(nn.Module):
    def __init__(self, d_model, dropout=0.0):
        super().__init__()
        self.fc1 = nn.Linear(d_model, 4 * d_model)   # 4 倍扩维：GPT 系惯例
        self.gelu = nn.GELU()                        # 平滑 ReLU，梯度无断点
        self.fc2 = nn.Linear(4 * d_model, d_model)
        self.drop = nn.Dropout(dropout)
    def forward(self, x):
        return self.drop(self.fc2(self.gelu(self.fc1(x))))
class Block(nn.Module):
    def __init__(self, d_model, n_head, block_size, dropout):
        super().__init__()
        self.ln1 = nn.LayerNorm(d_model)
        self.attn = CausalSelfAttention(d_model, n_head, block_size, dropout)
        self.ln2 = nn.LayerNorm(d_model)
        self.mlp = MLP(d_model, dropout)
    def forward(self, x):
        # Pre-LN：归一化在子层之前，残差支路无归一化，梯度可直通底层
        x = x + self.attn(self.ln1(x))
        x = x + self.mlp(self.ln2(x))
        return x

class MiniGPT(nn.Module):
    def __init__(self, vocab_size, d_model=128, n_layer=4, n_head=4, block_size=256, dropout=0.1):
        super().__init__()
        self.block_size = block_size
        self.tok_emb = nn.Embedding(vocab_size, d_model)
        self.pos_emb = nn.Embedding(block_size, d_model)   # 可学习位置编码
        self.drop = nn.Dropout(dropout)
        self.blocks = nn.ModuleList([Block(d_model, n_head, block_size, dropout) for _ in range(n_layer)])
        self.ln_f = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, vocab_size, bias=False)
        self.head.weight = self.tok_emb.weight   # weight tying：输出头复用输入 embedding
        self.apply(self._init_weights)
    def _init_weights(self, m):
        # GPT-2 经验初始化：0.02 的正态分布；LayerNorm 默认参数已合适
        if isinstance(m, (nn.Linear, nn.Embedding)):
            nn.init.normal_(m.weight, mean=0.0, std=0.02)
            if isinstance(m, nn.Linear) and m.bias is not None:
                nn.init.zeros_(m.bias)
    def forward(self, idx, targets=None):
        B, T = idx.shape
        pos = torch.arange(0, T, dtype=torch.long, device=idx.device)
        x = self.drop(self.tok_emb(idx) + self.pos_emb(pos))   # 位置与 token 各占一维
        for block in self.blocks:
            x = block(x)
        logits = self.head(self.ln_f(x))          # (B, T, vocab_size)
        loss = None
        if targets is not None:
            # 拉平后交叉熵：每个位置都在预测下一个 token
            loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1))
        return logits, loss
```

### 3. 训练循环

循环本身只有十几行，但每个超参都有出处：AdamW 把 weight decay 与梯度更新解耦（L2 正则不再跟着自适应学习率走）；warmup 防止初期大梯度把刚初始化的权重带飞；cosine 衰减到 min_lr 收尾更平滑；clip_grad_norm 防 loss spike。get_batch 随机起点切窗口，等价于把长文档切成定长训练样本。

```python
import math
import torch
import torch.nn as nn

def get_batch(data, batch_size, block_size):
    # 从长序列随机起点切窗口；x 与 y 错开一位，y 是 x 的 next-token 目标
    ix = torch.randint(0, len(data) - block_size, (batch_size,))
    x = torch.stack([data[i:i + block_size] for i in ix])
    y = torch.stack([data[i + 1:i + 1 + block_size] for i in ix])
    return x, y
def lr_at(step, total, warmup=100, max_lr=3e-4, min_lr=3e-5):
    if step < warmup:
        return max_lr * (step + 1) / warmup          # 线性 warmup
    progress = (step - warmup) / (total - warmup)
    return min_lr + 0.5 * (max_lr - min_lr) * (1 + math.cos(math.pi * progress))
@torch.no_grad()
def estimate_loss(model, data, batch_size=32, iters=20):
    model.eval()
    total = 0.0
    for _ in range(iters):
        xb, yb = get_batch(data, batch_size, model.block_size)
        _, loss = model(xb, yb)
        total += loss.item()
    model.train()
    return total / iters
def train(model, data, val_data, steps=2000, batch_size=32):
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, betas=(0.9, 0.95), weight_decay=0.1)
    # AdamW：weight decay 从梯度更新中解耦，等价于每步对权重做指数衰减
    for step in range(steps):
        lr = lr_at(step, steps)
        for g in optimizer.param_groups:
            g['lr'] = lr
        xb, yb = get_batch(data, batch_size, model.block_size)
        logits, loss = model(xb, yb)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)   # 防 loss spike
        optimizer.step()
        if step % 200 == 0:
            print('step %d lr %.5f train %.4f val %.4f' % (step, lr, loss.item(), estimate_loss(model, val_data)))
    return model
```

### 4. top-p 采样生成

生成与训练唯一的区别是「从分布采样而非取 argmax」。temperature 先缩放 logits（越低分布越尖锐，0 即贪心解码）；top-p 保留累积概率达到 p 的最小 token 集合——比 top-k 更自适应，因为分布的「头部大小」随上下文变化。cutoff 的右移写法保证至少保留一个 token，边界情况不报错。

```python
import torch
import torch.nn.functional as F

@torch.no_grad()
def generate(model, idx, max_new_tokens, temperature=1.0, top_p=0.9):
    # idx: (1, T)。超长时截取最近 block_size 个 token（真实实现用 KV cache）
    for _ in range(max_new_tokens):
        idx_cond = idx if idx.size(1) <= model.block_size else idx[:, -model.block_size:]
        logits, _ = model(idx_cond)
        logits = logits[:, -1, :] / temperature   # temperature 越低分布越尖锐
        probs = F.softmax(logits, dim=-1)
        # top-p：按概率降序，保留累积概率刚超过 p 的最小集合
        sorted_probs, sorted_idx = torch.sort(probs, descending=True)
        cum = torch.cumsum(sorted_probs, dim=-1)
        cutoff = cum > top_p
        cutoff[:, 1:] = cutoff[:, :-1].clone()    # 右移一位：让「第一个超过」保留下来
        cutoff[:, 0] = False                      # 兜底：至少保留概率最大的 1 个
        sorted_probs = sorted_probs.masked_fill(cutoff, 0.0)
        sorted_probs = sorted_probs / sorted_probs.sum(dim=-1, keepdim=True)
        next_id = torch.multinomial(sorted_probs, num_samples=1)
        next_id = torch.gather(sorted_idx, dim=-1, index=next_id)
        idx = torch.cat([idx, next_id], dim=1)
    return idx

# 用法示意：
# toks = torch.tensor([bpe.encode('从前有座山')], dtype=torch.long)
# out = generate(model, toks, max_new_tokens=100, temperature=0.8, top_p=0.9)
# print(bpe.decode(out[0].tolist()))
```

## 深挖追问

- **Q：为什么 attention 要除以 sqrt(d_head)？** A：$q\cdot k$ 是 $d_{head}$ 个随机内积之和，各分量独立零均值时方差 $\propto d_{head}$；不缩放则 logits 尺度随维度增长，softmax 趋近 one-hot，梯度消失，训练变慢甚至不收敛。除 $\sqrt{d_{head}}$ 后方差归一为 1，这也是 FlashAttention 等后续实现都要保住的「scaling」。
- **Q：Pre-LN 和 Post-LN 怎么选？** A：Post-LN（原论文）是 $x_{l+1}=\mathrm{LN}(x_l+F(x_l))$，残差支路经过 LN，梯度被压缩，层深后训练初期不稳定，需要 careful init 与 warmup；Pre-LN 是 $x_{l+1}=x_l+F(\mathrm{LN}(x_l))$，残差直通，梯度可回传到底层，训练稳定，代价是输出端少一层归一化（所以补了 ln_f）。GPT-3 之后的主流 LLM 几乎都用 Pre-LN。
- **Q：weight tying 有什么好处？** A：embedding 与输出头共享权重，省 $V\times d$ 参数（大词表时占比可观）；更本质的是输入输出表示共享同一空间，初始 loss 有上界 $\ln V$，且「语义相近的 token 有相近输入输出表示」成为先验。
- **Q：小语料训练会观察到哪些现象？** A：初始 loss 约 $\ln 512\approx 6.24$；几十 KB 语料配 1M 参数，几十步后 train loss 快速下降，但 val loss 先降后升（过拟合）；模型开始逐字背出训练文本（memorization——参数容量远超语料信息量）；训练过久后采样出现重复循环（分布过尖锐）。这些是「容量 vs 数据量」的直观演示，面试中主动讲出来说明你真训过。
- **Q：loss spike 是什么、怎么办？** A：训练中后期 loss 突然飙高又回落。常见诱因：某个 batch 的极端样本遇上大学习率、Adam 二阶动量 stale、fp16 溢出。应对：梯度裁剪、降学习率、从 checkpoint 重启跳过该 batch、检查数据清洗。小模型实验里还常见「可逆性卡点」现象，与 grokking 同源。

## 面试加分点

- 全链路不依赖任何教程代码，现场手写因果 mask、top-p cutoff 与 weight tying；
- 报出初始 loss 的数学估计 $\ln V$，并与自己的训练曲线对照；
- 把 BPE 讲成压缩问题、把 temperature/top-p 讲成分布修正，而不是背参数表；
- 主动提扩展点：RoPE、GQA、FlashAttention、bfloat16 autocast、KV cache——展示你知道这条路通向工业实现；
- 用 val loss 的 U 形 + memorization 现象反推「为什么预训练需要海量数据」。''',
    },
    # ================================================================ proj-002
    {
        "id": "proj-002",
        "name": "FlashAttention：分块在线 softmax 简化实现",
        "domain": "transformer",
        "level": "进阶",
        "tags": ["注意力", "推理优化"],
        "summaryMd": r'''标准 attention 物化 N×N 分数矩阵，显存 O(N²)、HBM 读写三趟，是长上下文 OOM 与推理变慢的元凶。本项目给出可运行的 torch 分块实现，重点讲清推导链：safe softmax → online softmax 修正递推 → 分块 tiling → 因果 mask 分块表达，以及 O(N²d²/M) 的 IO 复杂度公式。面试时能现场推 online softmax 的 rescale 递推、报出具体显存数，是区分「背概念」与「真懂系统」的分水岭。''',
        "bodyMd": r'''## 背景与思路

标准 scaled dot-product attention 在序列长度 N 大时有两个痛点：**显存**上要物化 N×N 的分数矩阵 S 和 softmax 输出 P（O(N²)，反向传播还得保留）；**IO** 上 S 要写进 HBM、再读出来两次（一次算 max/sum、一次算 PV），三次往返让它成为典型的 memory-bound 操作——算力闲着，带宽打满。FlashAttention 的解法分两步：先用 safe softmax 与 online softmax 证明「算 softmax 不需要整行同时在场，只需要 running max 与 running sum」；再把 Q/K/V 分块，让每个块在 SRAM 内完成完整的「分数-归一-加权」流程，全程不落地 N×N 矩阵。显存降到 O(N)，HBM 访问量从 O(N²) 降到 O(N²d²/M)。

本项目的价值在推导链而非 kernel：torch 分块版跑不快（没有 CUDA fusion），但每一步都透明可查，能让你在面试里讲清「为什么能分块」。

## 架构设计

实现分四步递进，每步都是下一步的前提：

1. **基线**：naive attention，物化 S，作为正确性与显存对照；
2. **safe softmax**：减行最大值防上溢，指出它是「无需全局信息也能算 softmax」的前提；
3. **online softmax**：单遍扫描，用 running max/sum 的修正递推，替代「先 max 再 sum 再除」的两遍流程；
4. **分块 attention**：外层按行切 Q，内层按列切 K/V，逐块更新统计量，扫完全部列块后统一归一化写回 O；再加因果版本与数值对拍测试。

显存账：naive 存 S、P 两个 N×N 矩阵；分块版只存 O(N) 的 m/l 统计量与单块临时矩阵（Br×Bc）。

## 关键组件实现

### 1. 基线、safe softmax 与 online softmax

先立靶子：naive 实现的痛点是 S 物化 + HBM 三趟。safe softmax 减去行最大值，数学上不变（分子分母同除 $\exp(m)$），数值上把指数压到非正，杜绝上溢。online softmax 的关键是修正递推：新最大值到来时，旧累加和按「新旧 max 的指数差」回缩，从而单遍扫完即可得到最终分母。

```python
import math
import torch
import torch.nn.functional as F

def naive_attention(Q, K, V, mask=None):
    # 标准实现：物化 N*N 的 scores 与 softmax 输出
    # 痛点 1：显存 O(N^2)；痛点 2：S 要在 HBM 上写一次、读两次（算 max/sum、算 PV）
    scores = Q @ K.transpose(-2, -1) / math.sqrt(Q.size(-1))
    if mask is not None:
        scores = scores.masked_fill(mask == 0, float('-inf'))
    attn = F.softmax(scores, dim=-1)
    return attn @ V

def safe_softmax_row(x):
    # 减去行最大值再 exp：数值不变（分子分母同除 exp(m)），但避免 exp 上溢
    # fp16 最大约 65504，exp(80) 就溢出；fp32 下 exp(1000) 也变 inf
    m = x.max(dim=-1, keepdim=True).values
    e = torch.exp(x - m)
    return e / e.sum(dim=-1, keepdim=True)

def online_softmax(x):
    # 只扫一遍、只记 running max 与 running sum 就能算出 softmax
    # 关键递推：l_new = l_old * exp(m_old - m_new) + exp(x_j - m_new)
    # 因为 exp(x_i - m_old) = exp(x_i - m_new) * exp(m_new - m_old)
    B, N = x.shape
    m = torch.full((B, 1), float('-inf'))
    l = torch.zeros(B, 1)
    for j in range(N):
        col = x[:, j:j + 1]
        m_new = torch.maximum(m, col)
        l = l * torch.exp(m - m_new) + torch.exp(col - m_new)
        m = m_new
    return torch.exp(x - m) / l
```

### 2. 分块 attention（torch 版）

tiling 的做法：Q 按行切成 Br 大小的块，K/V 按列切成 Bc 大小的块，块对 (Qi, Kj) 在 SRAM 内完成内积、safe softmax 分子、累加，统计量 mi/li 跨块携带。注意 Oi 的修正项 `Oi * exp(mi - m_new)`：之前块的贡献按新 max 回缩，与 online softmax 的 l 递推是同一公式。扫完全部列块后统一除以 li，输出只在最后写一次 HBM。

```python
def flash_attention(Q, K, V, Br=64, Bc=64):
    # 分块在线 softmax：外层按行切 Q，内层按列切 K/V，逐块更新 running 统计量
    # 每个块只占 Br*Bc 的临时显存，全程不物化 N*N 矩阵
    B, N, d = Q.shape
    scale = 1.0 / math.sqrt(d)
    O = torch.empty_like(Q)
    m = torch.full((B, N), float('-inf'))   # 每行 running max
    l = torch.zeros(B, N)                   # 每行 running sum（softmax 分母）
    for i0 in range(0, N, Br):
        Qi = Q[:, i0:i0 + Br] * scale
        mi = m[:, i0:i0 + Br].unsqueeze(-1)
        li = l[:, i0:i0 + Br].unsqueeze(-1)
        Oi = torch.zeros(B, Br, d)
        for j0 in range(0, N, Bc):
            Kj = K[:, j0:j0 + Bc]
            Vj = V[:, j0:j0 + Bc]
            S = Qi @ Kj.transpose(-2, -1)          # 块内 scores (B, Br, Bc)
            m_new = torch.maximum(mi, S.max(dim=-1, keepdim=True).values)
            P = torch.exp(S - m_new)               # 块内 safe softmax 分子
            li = li * torch.exp(mi - m_new) + P.sum(dim=-1, keepdim=True)
            Oi = Oi * torch.exp(mi - m_new) + P @ Vj   # 旧贡献按新 max 回缩
            mi = m_new
        O[:, i0:i0 + Br] = Oi / li                 # 扫完全部列块后统一归一化
        m[:, i0:i0 + Br] = mi.squeeze(-1)
        l[:, i0:i0 + Br] = li.squeeze(-1)
    return O
```

### 3. 因果版本与数值对拍

因果版只改两处：内层循环只扫到对角块（$j\le i$ 的列块，省掉一半以上计算），对角块内再按行 mask 掉右上三角。简化假设 Br == Bc，使对角块与行块起点对齐。对拍测试用 tril mask 的 naive 结果做基准——分块版在 fp32 下应与之几乎一致（1e-5 量级），这证明 rescale 递推在数学上等价。

```python
def flash_attention_causal(Q, K, V, Br=64, Bc=64):
    # 因果版：内层循环只扫到对角块（j <= i），对角块内再按行 mask
    # 简化假设 Br == Bc，对角块与行块起点 i0 对齐
    B, N, d = Q.shape
    scale = 1.0 / math.sqrt(d)
    O = torch.empty_like(Q)
    m = torch.full((B, N), float('-inf'))
    l = torch.zeros(B, N)
    for i0 in range(0, N, Br):
        Qi = Q[:, i0:i0 + Br] * scale
        mi = m[:, i0:i0 + Br].unsqueeze(-1)
        li = l[:, i0:i0 + Br].unsqueeze(-1)
        Oi = torch.zeros(B, Br, d)
        for j0 in range(0, min(i0 + Br, N), Bc):
            Kj = K[:, j0:j0 + Bc]
            Vj = V[:, j0:j0 + Bc]
            S = Qi @ Kj.transpose(-2, -1)
            if j0 == i0:
                row = torch.arange(Br).unsqueeze(1)
                col = torch.arange(Bc).unsqueeze(0)
                S = S.masked_fill(col > row, float('-inf'))   # 屏蔽 j > i
            m_new = torch.maximum(mi, S.max(dim=-1, keepdim=True).values)
            P = torch.exp(S - m_new)
            li = li * torch.exp(mi - m_new) + P.sum(dim=-1, keepdim=True)
            Oi = Oi * torch.exp(mi - m_new) + P @ Vj
            mi = m_new
        O[:, i0:i0 + Br] = Oi / li
        m[:, i0:i0 + Br] = mi.squeeze(-1)
        l[:, i0:i0 + Br] = li.squeeze(-1)
    return O

if __name__ == '__main__':
    torch.manual_seed(0)
    B, N, d = 2, 128, 32
    Q = torch.randn(B, N, d)
    K = torch.randn(B, N, d)
    V = torch.randn(B, N, d)
    mask = torch.tril(torch.ones(N, N, dtype=torch.bool)).unsqueeze(0)
    ref = naive_attention(Q, K, V, mask)
    out = flash_attention_causal(Q, K, V, Br=32, Bc=32)
    print('max diff:', (ref - out).abs().max().item())
    memory_estimate(4096, 128)
```

### 4. 显存与 IO 复杂度

显存账一目了然：naive 要两个 N×N 矩阵，N=4096 时每头每样本就是 64MB（fp16），32 头乘 batch 直接爆卡；分块版只留 O(N) 统计量。IO 复杂度上，标准实现 HBM 访问量 O(Nd + N²)，分块版 O(N²d²/M)，M 是 SRAM 容量——因为每对块的读写量约 Br·Bc·d，块对数约 (N/Br)(N/Bc) ≈ N²/M。

```python
def memory_estimate(N, d, bytes_per_elem=2):
    # 每头每样本的中间激活显存估算（fp16）
    naive = 2 * N * N * bytes_per_elem          # S 和 P 两个 N*N 矩阵
    flash = (2 * N + 64 * 64) * bytes_per_elem  # m/l 统计量 + 单块 S 峰值
    print('N=%d: 标准 %.1f MB vs 分块 %.2f KB' % (N, naive / 1e6, flash / 1e3))
```

## 深挖追问

- **Q：safe softmax 为什么安全？** A：softmax 分子分母同乘 $\exp(-m)$ 不变；减去行最大后指数全部非正，最大是 $\exp(0)=1$，永不溢出。fp16 表示范围约 ±65504，不处理时 $\exp(80)$ 就溢出成 inf，一行全是 inf 后 softmax 变成 nan。下溢（远小于 max 的项变 0）对结果无实质影响。
- **Q：online softmax 的递推怎么推？** A：设 $l_{new}=\sum_{i\le j}\exp(x_i-m_{new})$，拆成旧项与新项：旧项 $\exp(x_i-m_{new})=\exp(x_i-m_{old})\cdot\exp(m_{old}-m_{new})$，求和即 $l_{old}\cdot\exp(m_{old}-m_{new})$；新项直接 $\exp(x_j-m_{new})$。所以统计量 (m, l) 可以流式携带，这是分块正确性的全部数学。
- **Q：为什么 backward 也要专门设计？** A：标准 autograd 要为 softmax 反传保留 S 或 P，仍是 O(N²) 激活；FlashAttention 的 backward 不存全局 P，而是按块重算 S，配合 forward 阶段已存的 m/l 统计量完成梯度，显存保持 O(N)，同时整条链 fused 成一个 kernel，HBM 往返进一步减少。
- **Q：IO 复杂度 O(N²d²/M) 怎么理解？** A：M 是 SRAM 容量。每对块 (Qi, Kj) 要读写约 Br·Bc·d 字节，块对数约 (N/Br)(N/Bc)；让 Br·Bc ≈ M 最大化利用 SRAM，则块对数 ≈ N²/M，总访问 ≈ (N²/M)·M·d²/N² 量级再乘常数，即 O(N²d²/M)。M 远大于 d 时相对 O(N²) 下降 1~2 个数量级。
- **Q：生产上怎么用，还要自己写 kernel 吗？** A：不需要。torch 2.0 起的 scaled_dot_product_attention 自动在 flash / memory-efficient 后端间选择；flash-attn 库支持 varlen、GQA、paged KV cache；需要自定义 mask 的场景用 flex_attention。自己写 tiling 的意义是理解原理，而不是替代 CUDA kernel。
- **Q：分块实现的数值精度够吗？** A：rescale 递推在数学上等价于精确 softmax，fp32 下与 naive 的误差约 1e-5；实现上统计量 m/l 与累加器用 fp32，块内 P 可用 fp16，训练可接受。这是 flash kernel 内部坚持 fp32 accumulate 的原因。

## 面试加分点

- 现场推导 online softmax 的修正递推，而不是复述「分块 + 在线统计」八个字；
- 讲清 HBM/SRAM 两级存储的数据流与 O(N²d²/M) 公式的含义；
- 知道三个实现细节：backward 块内重算 S、fp32 累加、causal 版跳过右上三角块；
- 报出具体数字：N=4096 时标准 attention 每头每样本 64MB（两个 N×N 矩阵），说明长上下文 OOM 的账；
- 落地建议：默认用 SDPA，自定义 mask 才上 flex_attention，展示工程判断力。''',
    },
    # ================================================================ proj-003
    {
        "id": "proj-003",
        "name": "LoRA/QLoRA 微调最小实现",
        "domain": "posttrain",
        "level": "经典",
        "tags": ["微调", "PEFT"],
        "summaryMd": r'''手写 LoRA 线性层（A 高斯初始化、B 零初始化、alpha/r 缩放），并演示挂载到 HuggingFace 模型的递归替换、参数冻结、合并部署与 adapter 保存的完整闭环，附 QLoRA 的 NF4 与双量化原理代码。做完能精确报出全参微调 84GB 与 LoRA 适配器几 MB 的显存账，面试时讲清「B 为什么必须零初始化」「alpha 本质是学习率」这两点最加分。''',
        "bodyMd": r'''## 背景与思路

全参微调 7B 模型需要权重 14GB + 梯度 14GB + Adam 状态 56GB ≈ 84GB，且每个任务都要存一份完整权重。LoRA 的洞察：微调只是对预训练权重做一个小幅修正，而实验观察这个修正矩阵 $\Delta W$ 的谱集中在少数奇异值上——所以用低秩分解 $\Delta W = BA$（$A\in\mathbb{R}^{r\times in}$，$B\in\mathbb{R}^{out\times r}$，$r\ll\min(in,out)$）表达它。收益立竿见影：可训练参数从 7B 降到几 M（r=8 时约 0.06%），优化器状态同步缩小，多个任务共享一个底座、只换几 MB 的 adapter，合并后推理零额外开销。

本项目手写核心层与完整工程闭环：挂载、冻结、训练、合并、保存；QLoRA 部分讲清 NF4 非均匀量化、双重量化与 paged optimizer 三个显存来源。

## 架构设计

数据流：冻结的预训练权重走原路径，旁路 $x\to A\to B\to$ 输出与之相加。工程闭环分五步：

1. **LoRALinear**：包装 nn.Linear，A 用高斯初始化、B 全零（起步时 $\Delta W=0$，模型行为与预训练完全一致）；
2. **挂载**：递归遍历模型，把名字含 q_proj/v_proj 的 Linear 替换成 LoRALinear（真实项目里模型来自 transformers，用占位接口注明）；
3. **训练**：冻结全部参数、只解冻 A/B，优化器只吃可训练参数；
4. **合并**：$W' = W + \frac{\alpha}{r}BA$，摘掉旁路后零推理开销；
5. **保存**：只存 A/B 与超参，多任务切换只换小文件。

## 关键组件实现

### 1. LoRA 线性层

两个初始化细节决定成败：A 必须随机（否则 A=0、B=0 时梯度对称，永远学不动）；B 必须全零（否则随机扰动污染预训练输出，早期训练不稳定）。scale = alpha/r 让调 r 时不必重调学习率。

```python
import torch
import torch.nn as nn

class LoRALinear(nn.Module):
    # 对目标 Linear 加低秩旁路：y = Wx + (alpha / r) * B(Ax)
    # A: (r, in) 高斯初始化；B: (out, r) 全零初始化，起步时 delta W = 0
    def __init__(self, in_features, out_features, r=8, alpha=16, dropout=0.0):
        super().__init__()
        self.r = r
        self.alpha = alpha
        self.scale = alpha / r          # 缩放系数；调 r 时用 alpha 保持量级稳定
        self.linear = nn.Linear(in_features, out_features)
        self.linear.weight.requires_grad_(False)   # 冻结预训练权重
        if self.linear.bias is not None:
            self.linear.bias.requires_grad_(False)
        self.lora_A = nn.Parameter(torch.randn(r, in_features) * 0.02)
        self.lora_B = nn.Parameter(torch.zeros(out_features, r))
        self.dropout = nn.Dropout(dropout)

    @classmethod
    def from_linear(cls, lin, r=8, alpha=16):
        # 包装一个已训练好的 Linear：拷贝权重，变成 LoRA 层
        lora = cls(lin.in_features, lin.out_features, r=r, alpha=alpha)
        lora.linear.weight.data.copy_(lin.weight.data)
        if lin.bias is not None:
            lora.linear.bias.data.copy_(lin.bias.data)
        return lora

    def forward(self, x):
        # x: (..., in)。先降到 r 维（过 A），再升回 out 维（过 B）
        delta = self.dropout(x @ self.lora_A.t()) @ self.lora_B.t()
        return self.linear(x) + self.scale * delta
```

### 2. 挂载到 HuggingFace 模型 + 参数冻结

挂载的本质是「按名字做图手术」：HF 模型的注意力层命名稳定（self_attn.q_proj 等），递归 named_children 就能定位替换。真实项目中的模型加载用 transformers 占位接口，版本不同签名略有差异，挂载逻辑不变。

```python
def apply_lora_to_linear(module, r=8, alpha=16, target=('q_proj', 'v_proj')):
    # 递归替换：把名字里含 q_proj / v_proj 的 Linear 换成 LoRALinear
    # 真实项目里模型来自 transformers（占位）：
    #   from transformers import AutoModelForCausalLM
    #   model = AutoModelForCausalLM.from_pretrained('Qwen/Qwen2.5-0.5B')
    for name, child in module.named_children():
        if isinstance(child, nn.Linear) and any(t in name for t in target):
            setattr(module, name, LoRALinear.from_linear(child, r=r, alpha=alpha))
        else:
            apply_lora_to_linear(child, r=r, alpha=alpha, target=target)
    return module

def mark_only_lora_trainable(model):
    # 双保险：先冻结全部参数，再只解冻 LoRA 的 A/B
    for p in model.parameters():
        p.requires_grad_(False)
    for name, p in model.named_parameters():
        if 'lora_A' in name or 'lora_B' in name:
            p.requires_grad_(True)

def build_optimizer(model, lr=1e-4):
    # 只有 A/B 进优化器：Adam 状态从「7B 参数 x 8 字节」缩到几 MB
    trainable = [p for p in model.parameters() if p.requires_grad]
    return torch.optim.AdamW(trainable, lr=lr)
```

### 3. 合并部署与 adapter 保存

合并是 LoRA 独有的部署优势：训练完把旁路吸收进权重，推理与全参模型完全一致、零延迟；保存只存 A/B，一个底座挂多个任务的 adapter，切换零成本。

```python
def merge_lora(model):
    # 合并部署：W' = W + (alpha/r) * B @ A，之后摘掉旁路，推理零额外开销
    # （合并后通常导出权重，加载回普通模型再推理）
    for module in model.modules():
        if isinstance(module, LoRALinear):
            delta = module.scale * (module.lora_B @ module.lora_A)  # (out, in)
            module.linear.weight.data += delta

def save_adapter(model, path):
    # 只存 A/B：几 MB 级别；一个底座可挂多个任务的 adapter，切换零成本
    state = {}
    for name, p in model.named_parameters():
        if 'lora' in name:
            state[name] = p.detach().cpu()
    torch.save({'state': state, 'r': 8, 'alpha': 16}, path)

def count_trainable(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
```

### 4. QLoRA：NF4 与双量化

QLoRA 在 LoRA 基础上再压显存，三件套：4-bit NF4 权重（反传时 dequant 成 fp16 再算，不存 4bit 权重的梯度）、双重量化（第 1 层量化产生的 fp32 块 scale 再量化成 8bit）、paged optimizer（优化器状态放 CPU 分页换入换出）。NF4 与 FP4 的区别：权重近似正态分布、信息集中在 0 附近，FP4 均匀网格在两端浪费量化点，NF4 用分位数构造 0 附近更密的非均匀网格，同 4bit 下误差明显更小。生产环境用 bitsandbytes，这里给原理简化版。

```python
import torch

def quant_4bit_symmetric(w, bits=4):
    # 4-bit 量化原理简化版：对称均匀网格
    # NF4 的区别：量化点来自 N(0,1) 的分位数，0 附近更密，贴合权重分布
    # 生产环境用 bitsandbytes 的 NF4（占位接口）：
    #   from bitsandbytes.nn import Linear4bit
    levels = 2 ** bits
    m = w.abs().max()                       # 每块独立 scale（真实实现按 64 个元素分块）
    scale = m / (levels // 2 - 1)
    q = torch.clamp(torch.round(w / scale), -(levels // 2 - 1), levels // 2 - 1)
    return q.to(torch.int8), scale

def dequant(q, scale):
    return q.float() * scale

def double_quant(block_scales, bits=8):
    # 双重量化：第 1 层量化产生的 fp32 block scale 们，本身再量化成 8bit
    # 显存从「每块 4 字节」压到「每块 1 字节 + 一个全局 fp32」
    s = block_scales.float()
    s_max = s.abs().max()
    q = torch.round(s / s_max * 127).clamp(-127, 127).to(torch.int8)
    return q, s_max

# 前向还原（概念顺序）：
#   block_scales = dequant(q_scale, global_s)   # 8bit -> fp32 块 scale
#   w_hat = dequant(w_q, block_scales)          # 4bit -> fp16 权重，再正常前向
# 反传时对 dequant 后的权重算梯度，不存 4bit 权重的梯度
```

### 5. 超参经验（rank / alpha / 目标模块）

- **rank**：8~64 起步；容量不足（下游指标上不去、新知识学不会）时先提 rank 再提 lr。rank 过大会退化成近似全参、过拟合风险上升；
- **alpha**：常用 alpha = 2r；合并后 alpha/r 被吸收进权重，所以 alpha 本质是「学习率的一部分」，两者不必同时大改；
- **目标模块**：q+v 起步（论文默认），扩展到 k、o 与 MLP 的 gate_proj/up_proj 通常带来稳定提升；down_proj 与 embedding 可选，新语言/新领域任务建议加上 embedding；
- **lr**：1e-4 量级，比全参微调大——因为 A/B 是全新随机参数，需要更大的步长；
- **数据**：指令跟随、风格对齐等「已有能力的重组合」LoRA 与全参差距很小；需要注入大量新知识（新语言、新领域）时低秩容量不够，差距显现，此时考虑全参或更高秩。

## 深挖追问

- **Q：为什么 B 必须零初始化？** A：$\Delta W=BA$，B=0 时训练第一步等价于原模型，不会因随机扰动破坏预训练能力；若 A、B 都随机，初始输出被噪声污染，早期训练不稳定。A 必须随机：否则 A=0、B=0 时两个零矩阵的梯度对称，训练永远停在原地（秩坍塌问题）。
- **Q：alpha 到底起什么作用？** A：$\Delta W$ 乘 alpha/r。r 增大时每列贡献被摊薄，用 alpha 保持总缩放量级稳定，让「调 r」与「调 lr」解耦。合并后 alpha/r 被吸收进权重矩阵，所以 alpha 本质上是学习率的一部分——这个说法能显出你对公式的理解层次。
- **Q：为什么低秩修正就够用？** A：预训练权重已经占据高维空间的好位置，微调只是在其附近找一个方向性修正；实验观察 $\Delta W$ 的奇异值集中在少数主方向上。也可以从隐式正则理解：r 限制了搜索空间，天然抗过拟合，这也是 LoRA 在小数据上往往优于全参的原因之一。
- **Q：QLoRA 省显存的三件套各省在哪？** A：4-bit NF4 权重把主干从 16bit 压到 4bit，省权重与加载带宽；双重量化把块 scale 从 fp32 压到 8bit + 全局标量；paged optimizer 把优化器状态放 CPU 分页换入换出。反传时 4bit 权重 dequant 成 fp16 再算梯度，梯度不落盘。7B 全参约 84GB，QLoRA 单卡 24GB 能跑。
- **Q：NF4 为什么比 FP4 好？** A：权重近似 N(0, σ²)，信息集中在 0 附近；FP4 是均匀网格，在两端的大数值处浪费量化点，0 附近反而精度不足；NF4 从标准正态分位数构造非均匀网格，0 附近量化点更密，同 4bit 下量化误差明显更小。
- **Q：LoRA 与全参微调什么时候差距大？** A：需要注入大量新知识（新语言、大量新事实、新领域）时低秩容量不足；风格迁移、指令跟随、格式对齐等「已有能力的重组合」差距很小。对策：提 rank、扩目标模块（含 embedding）、或直接全参。变体 DoRA（分解幅度与方向）、PiSSA（初始化用主奇异方向）就是在补低秩的表达力。

## 面试加分点

- 手写 LoRALinear + from_linear 挂载 + merge + save 的完整闭环，而不是只会调 peft 库；
- 精确的显存账：全参 7B ≈ 84GB（14 权重 + 14 梯度 + 56 Adam）vs LoRA 适配器 16MB + 极小优化器状态；
- alpha/r 讲出「合并后吸收、本质是学习率」的层次；
- 说出 NF4 分位网格、双量化、paged optimizer 三个 QLoRA 细节及其省显存分工；
- 知道 DoRA/PiSSA 等变体的一句话定位，展示跟进前沿而不只背原论文。''',
    },
    # ================================================================ proj-004
    {
        "id": "proj-004",
        "name": "GRPO 简化训练循环",
        "domain": "rl",
        "level": "前沿",
        "tags": ["强化学习", "RLVR"],
        "summaryMd": r'''GRPO 是 DeepSeek-R1 系列的核心 RL 算法：去掉与 policy 同规模的 critic，用「同 prompt 采 G 条回答、组内标准化 reward」直接估计优势。本项目实现完整训练循环：组采样、组内优势、clip surrogate、k3 KL 估计、数学题验证器 reward，并给出与 PPO 的显存对比账。面试时能写出 group advantage + clip + k3 的 loss、说清 RLVR 与 RM 路线的分工边界，是 2025 年之后 RL 岗位的必备技能点。''',
        "bodyMd": r'''## 背景与思路

PPO 做 RLHF 需要四个网络：policy、ref、reward、critic（价值网络），其中 critic 与 policy 同规模，显存翻倍，而且 value loss 与 policy loss 互相干扰、训练不稳。GRPO 的洞察：优势函数 $A=r+\gamma V(s')-V(s)$ 里 critic 的作用只是提供一个 baseline 降低方差；如果对同一个 prompt 采样 G 条回答，组内 reward 均值天然就是一个 baseline——同组样本的期望收益估计，做标准化后即相对优势。于是 critic 整个删掉，显存省一半，训练更稳，代价是采样成本变成 G 倍。配合 RLVR（可验证奖励：数学题答案对错、代码单测通过与否），reward 无标注噪声，成为 DeepSeekMath 与 DeepSeek-R1 的标配路线。

本项目的价值是把「论文里的公式」落成「能跑的训练循环」，并讲清每一步的动机与边界。

## 架构设计

训练循环分五步，对应五个组件：

1. **组采样**：同 prompt 采 G 条回答（G 控制优势估计方差，~1/√G）；
2. **reward**：RLVR 验证器打分（格式分 + 答案分），纯规则、无模型；
3. **组内优势**：reward 做组内 z-score，正值代表优于组均值；
4. **loss**：与 PPO 同构的 clipped surrogate + beta·KL（k3 估计器，锚定 ref 模型防 reward hacking）；
5. **更新**：逐条（或打包成 batch）反传，ref 模型只前向不反传。

显存对比：PPO 四模型 vs GRPO 两模型，省掉整个 critic 的参数与优化器状态。

## 关键组件实现

### 1. 组采样与数学验证器 reward

组采样的关键是「同 prompt 不同回答才可比」——跨 prompt 的 reward 尺度差异（难题普遍低分、易题普遍高分）会污染优势估计。验证器给 0.1 格式分 + 1.0 答案分，稀疏化防「刷格式」；答案匹配用 boxed 提取，简化版不支持嵌套花括号。

```python
import re
import torch

def reward_math(answer_text, gold):
    # RLVR 可验证奖励：格式分 0.1 + 答案分 1.0，避免连续打分的噪声
    r = 0.0
    if '\\boxed{' in answer_text:
        r += 0.1                                # 鼓励把最终答案放进 boxed
    match = re.findall(r'\\boxed\{([^{}]*)\}', answer_text)
    if match and match[-1].strip() == str(gold).strip():
        r += 1.0
    return r

def sample_group(policy, prompt_ids, G=8, max_new_tokens=64):
    # 同一个 prompt 采样 G 条回答组成一组；组内相对比较给出优势
    # G 越大优势估计方差越小（~1/sqrt(G)），但采样成本线性上升
    return [policy.generate(prompt_ids, max_new_tokens=max_new_tokens, do_sample=True)
            for _ in range(G)]

def group_advantage(rewards):
    # 组内 z-score 即优势：不需要 critic 拟合 baseline，组均值就是 baseline
    # 天然消除不同 prompt 的奖励尺度差异（有些题 reward 普遍高，有些普遍低）
    std = rewards.std()
    if std < 1e-8:
        return torch.zeros_like(rewards)        # 全对/全错组：无差异，梯度为零
    return (rewards - rewards.mean()) / std
```

### 2. 序列 logprob 与 GRPO loss

seq_logprob 是占位接口（transformers 风格），关键细节是「预测 answer 第 t 个 token 的 logit 位置是 len(prompt) - 1 + t」——拼接后一次前向，answer 段逐 token gather。loss 与 PPO 的 clipped surrogate 同构；KL 项用 k3 估计器，恒非负、无偏，二阶逼近 KL。

```python
import torch
import torch.nn.functional as F

def seq_logprob(model, prompt_ids, answer_ids):
    # 占位接口（transformers 风格）：拼接后一次前向，只对 answer 段计 logprob
    # 关键细节：answer 第 t 个 token 由位置 len(prompt) - 1 + t 的 logits 预测
    ids = torch.cat([prompt_ids, answer_ids], dim=-1)      # (1, T + T_a)
    logits = model(ids).logits
    logp = F.log_softmax(logits, dim=-1)
    start = prompt_ids.size(-1) - 1
    picked = logp[0, start + torch.arange(answer_ids.size(-1)), answer_ids[0]]
    return picked.sum()

def grpo_loss(logps_old, logps_new, adv, ref_logps, clip=0.2, beta=0.04):
    # 目标：组内优势最大化 + KL 惩罚，与 PPO 的 clipped surrogate 同构
    ratio = torch.exp(logps_new - logps_old)
    surr1 = ratio * adv
    surr2 = torch.clamp(ratio, 1 - clip, 1 + clip) * adv
    pg = torch.min(surr1, surr2)                # 取 min：保守更新，防一步走太远
    # k3 估计器：r = log pi_ref - log pi_new（即 q/p，q=ref，p=当前策略）
    # k3 = (q/p - 1) - log(q/p) = exp(r) - r - 1，逐 token 恒非负、无偏（采样自 pi_new）
    r = ref_logps - logps_new
    kl = torch.exp(r) - r - 1
    return (-pg + beta * kl).mean()
```

### 3. 训练循环

循环主体五步清晰：组采样 → reward → 组内优势 → 逐条算 loss 更新。两个实现细节：logps_old 必须 detach（ratio 的分母是采样时策略的 logp，不算梯度）；ref_model 在 no_grad 里只前向。骨架里逐条更新，工程上把 G 条拼成一个 batch 一次反传。

```python
def grpo_step(policy, ref_model, tasks, optimizer, G=8, beta=0.04, clip=0.2):
    # tasks: [(prompt_ids, 标准答案), ...]，一个 mini-batch 的题目
    # policy 与 ref_model 同结构；ref 只前向不反传，作为 KL 锚点
    total, n = 0.0, 0
    for prompt_ids, gold in tasks:
        answers = sample_group(policy, prompt_ids, G=G)          # 1. 组采样
        texts = [policy.decode(a) for a in answers]              # 占位：tokenizer.decode
        rewards = torch.tensor([reward_math(t, gold) for t in texts])
        adv = group_advantage(rewards)                           # 2. 组内优势
        logps_old = torch.stack(
            [seq_logprob(policy, prompt_ids, a) for a in answers]).detach()
        with torch.no_grad():
            ref_lps = torch.stack(
                [seq_logprob(ref_model, prompt_ids, a) for a in answers])
        # 3. 逐条更新（简化版；工程上把 G 条拼成 batch 一次反传）
        for a, lp_old, a_i, rlp in zip(answers, logps_old, adv, ref_lps):
            lp_new = seq_logprob(policy, prompt_ids, a)
            loss = grpo_loss(lp_old, lp_new, a_i, rlp, clip=clip, beta=beta)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total += loss.item()
            n += 1
    return total / n
```

### 4. 与 PPO 的显存对比

```python
def count_params(model):
    return sum(p.numel() for p in model.parameters())

# 显存对比（7B 模型，fp16 权重 + Adam 状态，数量级示意）：
# PPO：policy + ref + reward + critic 共 4 个 7B 级网络
#      critic 与 policy 同规模，参数与优化器状态都翻倍
# GRPO：只有 policy + ref 两个网络，无 value 网络
#      优势来自组内 reward 统计，省掉整个 critic 的显存与训练不稳定源
# 结论：同等显存下 GRPO 能容纳更大的 G 或更大的 policy
```

## 深挖追问

- **Q：GRPO 为什么能去掉 critic？** A：PPO 的 critic 用来估计 baseline V 以算优势 $A=r+\gamma V(s')-V(s)$；GRPO 用「同 prompt 的 G 条回答」构造对照组，组内 reward 均值就是 baseline，标准化后即优势。省掉与 policy 同规模的 value 网络，显存与训练不稳定源同时减少；代价是采样成本 G 倍，baseline 质量依赖 G。
- **Q：组内标准化的数学意义？** A：$A_i=(r_i-\mu_g)/\sigma_g$ 只依赖相对排序，天然免疫不同 prompt 的奖励尺度差异；$\sigma_g$ 还充当自适应步长——组内分歧大时梯度温和，分歧小时放大。全对/全错组 $\sigma\approx0$，优势全零，该组不产生有效更新（代码里显式处理了除零）。
- **Q：clip 和 PPO 里的一样吗？** A：完全同构。ratio = π_new/π_old 偏离 1 意味着一步更新过大，clip 到 [1−ε, 1+ε] 后取 min，把大步长截断成保守目标，防止策略突变破坏已有能力。GRPO 只是换了优势的估计方式，surrogate 目标没变。
- **Q：KL 惩罚为什么必要？k3 是什么？** A：验证器/RM 有盲区（长度、格式、谄媚），纯 reward 优化会 exploit 盲区导致 reward hacking；KL 惩罚把策略锚在参考分布附近。k3 = (q/p − 1) − log(q/p)（p 为当前策略、q 为 ref，即 exp(r) − r − 1，r = log q − log p），是 Schulman 总结的无偏估计器之一，逐 token 恒非负、二阶逼近 KL；k1 会出现负样本、方差大，故 DeepSeekMath 选 k3。
- **Q：G 取多少合适？** A：优势估计的噪声随 G 按 ~1/√G 下降；DeepSeek 系列论文中 G 取 16~64，复现实验常用 8~16。G 与 batch size 的乘积决定采样吞吐，工程上按「优势估计质量 vs 训练速度」折中，且 G 大时组内更容易出现全对/全错（浪费梯度）。
- **Q：为什么数学题适合 RLVR，边界在哪？** A：答案可程序验证（字符串匹配、符号对拍、测试用例），reward 无标注噪声，天然适合 GRPO；代码题用单测同样客观。主观任务（写作、对话、创意）没有可靠验证器，仍需 RM 或 LLM-as-judge，这是 GRPO 的主要适用边界——面试时主动说边界比只会吹算法更加分。

## 面试加分点

- 完整写出 group advantage + clip surrogate + k3 KL 的 loss 与更新循环；
- 讲清 RLVR 与 RM 路线的分工与适用边界，并能举出代码题单测的扩展；
- 对 G 与优势估计方差有 1/√G 的量化直觉；
- 报出 PPO 四模型 vs GRPO 两模型的显存账，落到「critic 与 policy 同规模」这个点上；
- 知道 reward 设计的坑：格式奖励权重过高会诱导先刷格式再刷正确率，奖励需稀疏化与归一化。''',
    },
    # ================================================================ proj-005
    {
        "id": "proj-005",
        "name": "奖励模型训练 + PPO 微调骨架",
        "domain": "posttrain",
        "level": "经典",
        "tags": ["RLHF", "对齐"],
        "summaryMd": r'''RLHF 的后两环：先训奖励模型（Bradley-Terry 成对损失 + 数据构造清洗 + 过拟合监控），再接 PPO 微调骨架（rollout、reward、KL 惩罚、GAE 优势、critic 更新）。本项目把「人类偏好 → 标量信号 → 策略更新」整条链的关键代码写出来，面试时能手推 BT 梯度、用 acc/margin/length-bias 三个指标讲 RM 健康度，是聊对齐项目时的核心储备。''',
        "bodyMd": r'''## 背景与思路

RLHF 分三环：SFT → 奖励模型（RM）→ PPO。RM 解决的核心问题：人类偏好没法直接当梯度，先把它压成标量信号。为什么做成对比较而不是绝对打分？标注者对「哪个更好」的判断稳定，对「好多少」的打分方差大且跨标注者尺度不一致；Bradley-Terry 模型把偏好建模成 sigmoid 概率，只学序关系，天然对尺度不敏感。PPO 再拿 RM 当 reward，用 KL 惩罚锚在 SFT 分布附近，防止策略钻 RM 盲区（reward hacking）。

本项目的价值是把这条链的关键代码落下来：BT loss、成对数据构造与清洗、RM 过拟合三指标、PPO 五步骨架。

## 架构设计

两阶段，各有独立的数据流与训练目标：

1. **RM 训练**：数据是 (prompt, chosen, rejected) 三元组；主干加标量 head，末 token 输出整句打分；loss 是 −log σ(s_chosen − s_rejected)；监控 acc、margin、length-bias 三个健康度指标；
2. **PPO 微调**：四模型——policy（可训练）、ref（冻结，KL 锚点）、reward（冻结，打分）、critic（可训练，估计价值）；每轮 rollout 采样 → RM 打分 → 减 KL 惩罚 → GAE 算优势 → 联合更新 policy 与 critic。

## 关键组件实现

### 1. Bradley-Terry 成对损失

BT loss 最漂亮的特性是「自适应难例」：对 s_c 的梯度是 σ(s_r − s_c)，模型判断越离谱梯度越大；已经拉开差距的样本 σ 接近 0，几乎不产生梯度。等价变形 softplus(s_r − s_c) 常被追问，与 margin 分类同构。

```python
import torch
import torch.nn.functional as F

def bt_loss(rm, chosen_ids, rejected_ids):
    # Bradley-Terry 成对损失：P(chosen 优于 rejected) = sigmoid(s_c - s_r)
    # rm 输出 (B, T, 1) 的逐位置标量，取末 token 作为整句打分（占位接口，
    # 真实实现用 transformers 的 AutoModelForSequenceClassification 或自加 value head）
    s_c = rm(chosen_ids).logits[:, -1, 0]
    s_r = rm(rejected_ids).logits[:, -1, 0]
    return -F.logsigmoid(s_c - s_r).mean()

# 等价变形（面试常考）：
#   -log sigmoid(x) = softplus(-x) = log(1 + exp(-x))
# 对 s_c 的梯度 = sigmoid(s_r - s_c)：模型判断越离谱，梯度越大；
# 已经拉开差距的样本 sigmoid 接近 0，几乎不产生梯度（自适应难例）
```

### 2. 成对数据构造与清洗

数据构造的要点：chosen/rejected 必须来自同一 prompt（同分布比较才有意义）；一条「N 选排序」标注拆成 N−1 个相邻对，比全组合 C(N,2) 噪声小（跨等级的对比往往差距过大，学不到细节）；清洗掉长度差过大（格式差异而非质量差异）与几乎重复（无学习信号）的样本对。

```python
def build_pairs_from_ranking(ranking):
    # 一条「N 选排序」标注拆成 N-1 个相邻对
    # 相邻对比全组合 C(N,2) 噪声小：跨等级的对比往往质量差距过大，学不到细节
    pairs = []
    for i in range(len(ranking) - 1):
        pairs.append((ranking[i], ranking[i + 1]))
    return pairs

def jaccard(a, b):
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)

def clean_pair(ch, re, max_len_ratio=2.0, dup_th=0.9):
    # 清洗规则（工程经验）：
    # 1. 长度差 2 倍以上：多半是格式/截断差异而非质量差异，丢弃
    # 2. token 集合几乎相同：chosen/rejected 没区别，无学习信号，丢弃
    if len(ch) > max_len_ratio * len(re) or len(re) > max_len_ratio * len(ch):
        return False
    if jaccard(ch.split(), re.split()) > dup_th:
        return False
    return True

def make_dataset(rankings):
    # 构造 + 清洗一步到位；额外可做 chosen/rejected 位置 swap 增广防位置偏置
    pairs = []
    for ranking in rankings:
        for pair in build_pairs_from_ranking(ranking):
            if clean_pair(*pair):
                pairs.append(pair)
    return pairs
```

### 3. RM 过拟合监控

RM 训练的健康度看三个信号：acc（eval 停滞即过拟合）、margin（持续变大是过度自信、score 分布发散）、length-bias（显著为正说明 RM 在学「越长越好」，PPO 阶段必然 reward hacking 出长文）。后两个信号直接预告 PPO 阶段的表现。

```python
import math

def rm_metrics(rm, eval_pairs):
    # 健康度三指标之二：acc 与 margin
    # 过拟合信号：train acc -> 1 而 eval acc 停滞；margin 持续变大（过度自信）
    acc = 0.0
    margin = 0.0
    for ch, re in eval_pairs:
        s_c = rm(ch).logits[:, -1, 0].item()
        s_r = rm(re).logits[:, -1, 0].item()
        acc += 1.0 if s_c > s_r else 0.0
        margin += s_c - s_r
    n = len(eval_pairs)
    return acc / n, margin / n

def length_bias(rm, eval_pairs):
    # 第三个信号：score 差与长度差的皮尔逊相关
    # 显著为正说明 RM 在学「越长越好」，PPO 阶段必然 reward hacking 出长文
    xs, ys = [], []
    for ch, re in eval_pairs:
        xs.append(len(ch) - len(re))
        ys.append((rm(ch).logits[:, -1, 0] - rm(re).logits[:, -1, 0]).item())
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy + 1e-8)
```

### 4. PPO 微调骨架

骨架五步：rollout 采样 → RM 打分 → 减 KL 惩罚 → 优势估计 → 联合更新。这里给出 GAE 与 PPO objective 的完整实现；ppo_step 用整句标量 logp 压缩主链路（真实实现换成 (T,) 张量、advantage 换 gae 即可）。四个网络的角色：policy 可训练、ref 冻结出 KL 锚点、reward 冻结打分、critic 可训练估计价值。

```python
import torch
import torch.nn.functional as F

def ppo_rollout(policy, prompt_ids, n=8, max_new_tokens=64):
    # 1. rollout：当前策略采样一批回答（在线数据），无梯度
    return [policy.generate(prompt_ids, max_new_tokens=max_new_tokens, do_sample=True)
            for _ in range(n)]

def gae(rewards, values, gamma=1.0, lam=0.95):
    # 优势 = 带衰减的 TD 残差反向累积
    # lam=1 退化为蒙特卡洛（无偏高方差），lam=0 是 TD(0)（有偏低方差）
    # rewards 已包含逐 token 的 KL 惩罚；rewards/values 是 (T,) 张量
    adv = []
    g = 0.0
    for t in reversed(range(len(rewards))):
        next_v = values[t + 1] if t + 1 < len(values) else 0.0
        delta = rewards[t] + gamma * next_v - values[t]
        g = delta + gamma * lam * g
        adv.append(g)
    return torch.tensor(adv[::-1])

def ppo_objective(logps_old, logps_new, adv, values, returns, logits=None,
                  clip=0.2, vf_coef=0.5, ent_coef=0.01):
    ratio = torch.exp(logps_new - logps_old)
    pg1 = ratio * adv
    pg2 = torch.clamp(ratio, 1 - clip, 1 + clip) * adv
    policy_loss = -torch.min(pg1, pg2).mean()            # clip 双保险
    value_loss = 0.5 * (values - returns).pow(2).mean()  # critic 回归目标
    ent = 0.0
    if logits is not None:                               # 熵奖励防分布坍缩
        p = F.softmax(logits, dim=-1)
        ent = -(p * F.log_softmax(logits, dim=-1)).sum(-1).mean()
    return policy_loss + vf_coef * value_loss - ent_coef * ent

def ppo_step(policy, ref_model, reward_model, critic, prompt_ids, optimizer,
             kl_coef=0.05, clip=0.2):
    # 一轮 PPO 骨架。占位接口：policy.logprob / reward_model.score / critic.score
    # 骨架用整句标量 logp，真实实现换成 (T,) 张量并调用上面的 gae
    answers = ppo_rollout(policy, prompt_ids)                   # 1. rollout
    logps_old = torch.stack(
        [policy.logprob(prompt_ids, a) for a in answers]).detach()
    rw = torch.stack([reward_model.score(prompt_ids, a) for a in answers])   # 2. reward
    with torch.no_grad():
        ref_lp = torch.stack([ref_model.logprob(prompt_ids, a) for a in answers])
        values = torch.stack([critic.score(prompt_ids, a) for a in answers])
    kl = logps_old - ref_lp                                    # 3. KL 惩罚
    rewards = rw - kl_coef * kl
    adv = (rewards - rewards.mean()) / (rewards.std() + 1e-8)  # 4. 优势（简化版）
    for a, lp_old, v, r, ad in zip(answers, logps_old, values, rewards, adv):
        lp_new = policy.logprob(prompt_ids, a)                 # 5. 更新
        loss = ppo_objective(lp_old, lp_new, ad, v, r, clip=clip)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
```

## 深挖追问

- **Q：为什么 pairwise 而不是回归绝对分？** A：标注者对「哪个更好」判断稳定，对「好多少」打分方差大且跨标注者尺度不一致；BT 模型把偏好建模成 sigmoid 概率，只学序关系，天然对尺度不敏感。绝对分回归还会被标注者风格（宽松/严格）污染。
- **Q：BT loss 的梯度怎么推？** A：−log σ(s_c − s_r) 对 s_c 的梯度是 σ(s_r − s_c)，对 s_r 的梯度是 −σ(s_r − s_c)：模型判断越错梯度越大，且对称地拉高 chosen、压低 rejected。等价式 softplus(s_r − s_c)，与 margin 分类同构——这个推导能现场手推。
- **Q：RM 过拟合有哪些信号？** A：train acc 顶到 1 而 eval acc 停滞；margin 持续变大（过度自信，score 分布发散）；length-bias 相关显著为正；score 分布坍缩（对几乎所有样本打相近分，区分度下降）。后两个信号直接预告 PPO 阶段的 reward hacking，是「RM 训好了没有」的判断依据。
- **Q：数据构造有哪些讲究？** A：chosen/rejected 必须来自同一 prompt 同分布比较；排序标注拆相邻对而非全组合（噪声更小）；控制长度差与重复度；swap 增广防位置偏置；必要时按长度匹配采样防长度偏置。数据质量对 RM 的贡献大于网络结构微调。
- **Q：PPO 里 KL 惩罚的方向和理由？** A：reward = RM 打分 − β·KL(π_θ‖π_ref)，把策略锚在 SFT 分布附近，防 RM 盲区（长度、格式、谄媚）被 exploit；β 经验 0.02~0.2，训练中 reward 发散或回复变长时先调 β。ref 模型冻结，只前向算 logp。
- **Q：critic 与 GAE 的关系？** A：优势 A_t = δ_t + γλδ_{t+1} + (γλ)²δ_{t+2} + ...，δ 是 TD 残差；λ=1 是蒙特卡洛（无偏高方差），λ=0 是 TD(0)（有偏低方差），0.95 常用。critic 用 value loss 回归 returns 来学 V。GRPO 用组内均值替代 critic，是同一「baseline 降方差」思路的两种实现。
- **Q：PPO 和 DPO 怎么定位？** A：PPO 在线，rollout 出新数据多轮迭代，四模型、训练复杂，但上限高；DPO 离线，直接把 BT 目标改写成 policy 的损失，policy+ref 两模型即可，便宜稳定，但静态数据下通常不如多轮迭代的 PPO/online DPO。工程上「先 DPO 快速验证、再上 PPO/GRPO 冲上限」是常见节奏。

## 面试加分点

- 现场手推 BT 梯度与 softplus 等价，而不是只写 loss 一行；
- 用 acc/margin/length-bias 三个指标讲 RM 健康度，体现真实训过 RM 的工程感；
- 能报出 PPO 四模型各自角色与显存结构，并与 GRPO、DPO 横向对比；
- reward hacking 有具体实例（长文、格式堆砌、重复关键词、谄媚）与对应防御（KL、长度惩罚、reward 归一化）；
- 讲清 RM 数据从「多选排序」到「相邻对」的拆分逻辑与清洗规则。''',
    },
]

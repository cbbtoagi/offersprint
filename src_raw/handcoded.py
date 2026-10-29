# -*- coding: utf-8 -*-
# 手撕代码题库（纯数据，无业务逻辑）
# 覆盖：Attention 手写 / 位置与结构组件 / 解码策略 / Tokenizer / 训练组件 / 高频算法题 / 概率与采样 / CV 手撕

QUESTIONS = [

    # ---------------------------------------------------------------- Attention 手写
    {
        "id": "handcoded-001",
        "topic": "Attention 手写",
        "type": "手撕",
        "difficulty": 2,
        "frequency": 3,
        "companies": ["字节", "腾讯", "华为"],
        "years": ["2024", "2025"],
        "question": "手写单头 self-attention（scaled dot-product），要求支持 causal mask，并与 PyTorch 官方实现对拍。",
        "answerMd": r'''**思路一句话**：attention 就是「相似度打分 → softmax 归一 → 加权求和」，scaled dot-product 三个公式：$\text{scores}=\frac{QK^\top}{\sqrt{d}}$、$\text{attn}=\text{softmax}(\text{scores}+\text{mask})$、$\text{out}=\text{attn}V$。

**实现要点**：1）除以 $\sqrt{d}$ 是关键：$QK^\top$ 的方差随维度 $d$ 线性增大，不缩放会导致 softmax 进入饱和区、梯度消失；2）causal mask 用上三角 bool 矩阵，`masked_fill` 成 $-\infty$，让 softmax 后未来位置权重为 0（注意是对 key 维 softmax，即 dim=-1）；3）mask 必须在 softmax 之前加，且用 `-inf` 而不是大负数（大负数在 fp16 下可能仍分到权重）。

**易错点**：mask 方向搞反（应是未来不可见）；softmax 维度写错；忘记 keepdim 导致广播错位；`-inf` 行全 mask 时 softmax 输出 NaN（本例因果 mask 保证每行至少能看到自己）。

**复杂度**：scores 矩阵 $O(T^2 d)$，加权求和 $O(T^2 d)$，总时间 $O(T^2 d)$、显存 $O(T^2)$——这正是 FlashAttention 要优化的部分。

**追问**：为什么除 $\sqrt d$ 而不是 $d$？padding mask 和 causal mask 怎么叠加？$-\infty$ 在 fp16 下怎么办（可换 -65504 或加 -1e4 的负大数 + later 行处理）。''',
        "keyPoints": [
            "缩放因子是 sqrt(d_head)，来源于内积方差分析，防 softmax 饱和",
            "causal mask 在 softmax 前用 -inf 填上三角（含对角线以上）",
            "softmax 沿最后一维（key 维）归一化",
            "复杂度 O(T^2 d)，注意力矩阵显存 O(T^2)，是 FlashAttention 优化动机",
            "padding mask 与 causal mask 叠加时都转成加性 -inf mask",
        ],
        "followUps": [
            {"q": "为什么是除以 sqrt(d) 而不是 d？", "a": "设 q、k 各分量独立同分布均值 0 方差 1，内积 q·k 的方差为 d。方差随 d 线性增大，softmax 会趋近 onehot、梯度趋 0。除以 sqrt(d) 把内积方差拉回 1，保持 logits 尺度稳定。"},
            {"q": "如果一行被 mask 全空（padding query），softmax 会怎样？怎么处理？", "a": "全 -inf 行 softmax 得到 NaN（0/0）。工程上常见做法：给该行统一加一个可注意的占位（如允许注意自己或第 0 个位置），训练后反正会被 padding loss 屏蔽；或输出后用 padding mask 把无效位置清零。"},
        ],
        "code": {
            "lang": "python",
            "caption": "单头 scaled dot-product attention，含 causal mask 与官方实现对拍",
            "content": r'''import math
import torch
import torch.nn.functional as F

def single_head_attention(q, k, v, causal=False):
    # q, k, v: (B, T, D)
    d = q.size(-1)
    scores = q @ k.transpose(-2, -1) / math.sqrt(d)     # (B, T, T)
    if causal:
        T = q.size(1)
        mask = torch.triu(torch.ones(T, T, dtype=torch.bool), diagonal=1)
        scores = scores.masked_fill(mask, float('-inf'))  # 未来位置置 -inf
    attn = F.softmax(scores, dim=-1)                    # 对 key 维归一化
    return attn @ v, attn

if __name__ == '__main__':
    torch.manual_seed(0)
    B, T, D = 2, 4, 8
    q, k, v = torch.randn(B, T, D), torch.randn(B, T, D), torch.randn(B, T, D)
    out, attn = single_head_attention(q, k, v, causal=True)
    assert out.shape == (B, T, D)
    assert torch.allclose(attn.sum(-1), torch.ones(B, T), atol=1e-5)   # 每行概率和为 1
    assert torch.allclose(attn[0, 0], torch.tensor([1., 0., 0., 0.]), atol=1e-5)  # 首 token 只看自己
    ref = F.scaled_dot_product_attention(q, k, v, is_causal=True)      # 官方实现对拍
    assert torch.allclose(out, ref, atol=1e-5)
    print('single head attention ok')''',
        },
    },

    {
        "id": "handcoded-002",
        "topic": "Attention 手写",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 5,
        "companies": ["字节", "阿里", "智谱", "月之暗面"],
        "years": ["2024", "2025"],
        "question": "手写多头注意力 MultiHeadAttention 模块，要求支持 causal mask，说清每一步张量形状变化。",
        "answerMd": r'''**思路一句话**：多头 = 「把 D 维切成 h 个 d_head 维子空间，各算一遍 attention，再拼回去投影」，形状主线：`(B,T,D) → (B,h,T,d_head) → attention → (B,T,D)`。

**实现主线**：Q/K/V 用一个大 Linear 一次投影出 `3*D` 再 `chunk(3)`（也可三个小矩阵，等价）；`view(B,T,h,d).transpose(1,2)` 拆头，attention 后 `transpose(1,2).reshape(B,T,D)` 合头，最后过 output 投影。

**易错点**：1）拆头必须先 `view` 后 `transpose`，直接 `reshape` 会把同一头的通道切散（内存不连续，要用 `.contiguous()` 或 `reshape` 兜底）；2）scores 形状是 `(B,h,T,T)`，mask 要能广播到这个形状；3）除以的是 $\sqrt{d_{head}}$ 不是 $\sqrt D$；4）合头时 reshape 前 tensor 是非连续的，PyTorch 的 `.reshape` 会自动拷贝，`.view` 会直接报错。

**复杂度**：QKV 投影 $O(T D^2)$，attention $O(h T^2 d_{head})=O(T^2 D)$，输出投影 $O(TD^2)$。参数量 $4D^2$（三个投影 + output）。现代实现里 Q/K/V 合并成一次 GEMM 还能提高 GPU 利用率。

**实践补充**：LLaMA 系给 Q/K 加 bias 的情况很少（Qwen 给 QKV 加了 bias 用于稳定长度外推，是个例外），推理时注意力还可与 KV cache、GQA 结合（另两题展开）。

**追问**：为什么多头比单头好（不同子空间学不同关系，ensemble 效应）？h 怎么选（d_head 通常 64~128）？如何在多头里加 GQA（见 GQA 题）。''',
        "keyPoints": [
            "形状主线 (B,T,D)→(B,h,T,d_head)→attention→(B,T,D)，拆头先 view 后 transpose",
            "缩放用 sqrt(d_head)，scores 是 (B,h,T,T)",
            "合头 reshape 前张量非连续，用 transpose(1,2).reshape",
            "QKV 可合成一个大 Linear 投影 3D 再 chunk，等价且 kernel 更友好",
            "参数量 4*D^2，attention 计算量 O(T^2 D)",
        ],
        "followUps": [
            {"q": "为什么不能直接 view(B, T, h, d_head) 就当拆完头了？", "a": "view 只是重排逻辑维度，attention 需要头维度在前（B,h,T,d）以便对每个头独立做 batched matmul，所以还要 transpose(1,2)。反过来合头时 transpose 后内存不连续，必须 reshape/contiguous。"},
            {"q": "attention 输出的 dropout 加在哪里？", "a": "标准实现有两处可加：attention 权重上（attn prob dropout，原始论文做法）和 output 投影前。当前主流 LLM（如 LLaMA）通常只保留 output 处的 residual dropout，attn prob dropout 常设 0。"},
        ],
        "code": {
            "lang": "python",
            "caption": "多头注意力完整模块（QKV 合并投影 + causal mask）",
            "content": r'''import math
import torch
from torch import nn
import torch.nn.functional as F

class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, n_heads, causal=True, dropout=0.0):
        super().__init__()
        assert d_model % n_heads == 0
        self.h = n_heads
        self.d_head = d_model // n_heads
        self.causal = causal
        self.qkv = nn.Linear(d_model, 3 * d_model, bias=False)  # 一次投影出 Q/K/V
        self.proj = nn.Linear(d_model, d_model, bias=False)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, pad_mask=None):
        B, T, _ = x.shape
        q, k, v = self.qkv(x).chunk(3, dim=-1)          # 各 (B, T, D)
        # 拆头: (B,T,D) -> (B, h, T, d_head)
        q = q.view(B, T, self.h, self.d_head).transpose(1, 2)
        k = k.view(B, T, self.h, self.d_head).transpose(1, 2)
        v = v.view(B, T, self.h, self.d_head).transpose(1, 2)
        scores = q @ k.transpose(-2, -1) / math.sqrt(self.d_head)   # (B,h,T,T)
        if self.causal:
            m = torch.triu(torch.ones(T, T, dtype=torch.bool, device=x.device), 1)
            scores = scores.masked_fill(m, float('-inf'))
        if pad_mask is not None:                        # (B,1,1,T)，True 为 padding
            scores = scores.masked_fill(pad_mask, float('-inf'))
        attn = self.dropout(F.softmax(scores, dim=-1))
        out = (attn @ v).transpose(1, 2).reshape(B, T, -1)          # 合头回 (B,T,D)
        return self.proj(out)

if __name__ == '__main__':
    torch.manual_seed(0)
    mha = MultiHeadAttention(d_model=16, n_heads=4)
    x = torch.randn(2, 5, 16)
    out = mha(x)
    assert out.shape == x.shape
    assert sum(p.numel() for p in mha.parameters()) == 4 * 16 * 16   # qkv 3D^2 + proj D^2
    print('multi head attention ok')''',
        },
    },

    {
        "id": "handcoded-003",
        "topic": "Attention 手写",
        "type": "手撕",
        "difficulty": 4,
        "frequency": 5,
        "companies": ["字节", "月之暗面", "NVIDIA", "阿里"],
        "years": ["2024", "2025"],
        "question": "手写带 KV cache 的自回归解码 attention，并用「整段重算」的结果验证增量式计算等价。",
        "answerMd": r'''**思路一句话**：自回归解码时历史 token 的 K/V 不随新 token 变化，把它们缓存下来，每步只算新 token 的 q/k/v 并与 cache 拼接，把「每步重算全序列」的 $O(T^2)$ 降到「每步 $O(T)$ 增量」。

**实现主线**：1）prefill 阶段：整段 prompt 一次前向，K/V 写入 cache，可并行；2）decode 阶段：每步新 token 的 $q_t$ 与 cache 里全部 K 做内积，scores 形状 `(B,1,T+t)`，softmax 后对 V 加权求和，再把新 $k_t,v_t$ append 进 cache。

**易错点**：1）新的 K/V 必须先入 cache 再参与本次 attention（当前 token 也要看见自己）；2）mask 在增量阶段天然满足因果性（cache 只含过去），不需要再画三角 mask；3）cache 显存 = `2 × layers × kv_heads × T × d_head × dtype字节 × batch`，是长上下文推理的显存大头；4）batch 里不同序列长度不同时要 padding 或用变长管理（PagedAttention 思路）。

**复杂度**：decode 单步时间 $O(T\cdot D)$（有 cache）vs $O(T^2 D)$（无 cache 重算）；cache 显存 $O(L\cdot T\cdot D)$。GQA/MQA 就是通过减少 KV 头数把 cache 砍小。

**追问**：prefill 和 decode 的瓶颈分别是什么（preffill 算力、decode 访存/带宽）？为什么 decode 是 memory-bound（每步算量小、但要读全部权重和 cache）？continuous batching 怎么利用这一点。''',
        "keyPoints": [
            "K/V 不随新 token 变化，缓存后每步只算新 token 的 q/k/v",
            "新 K/V 要先拼进 cache 再做本次 attention，保证能看见自己",
            "decode 单步 O(T·D)，无 cache 重算是 O(T^2·D)",
            "KV cache 显存 = 2·layers·kv_heads·T·d_head·bytes·batch，长上下文显存大头",
            "增量解码天然满足因果 mask，无需额外三角 mask",
        ],
        "followUps": [
            {"q": "为什么 decode 阶段是 memory-bound？", "a": "decode 每步 batch 内 token 少、算术强度低，但要把全部模型权重和 KV cache 从 HBM 读一遍，耗时由带宽决定。因此大 batch、量化权重、GQA、投机解码（一次验证多 token 摊薄读取）都能提升 decode 效率。"},
            {"q": "KV cache 能否压缩？有哪些办法？", "a": "GQA/MQA 减少 KV 头数；KV cache 量化（INT8/FP8）；滑动窗口/局部注意力限制 cache 长度；PagedAttention 按页管理减少碎片；Cross-layer KV 共享（如 YOCO 思路）。"},
        ],
        "code": {
            "lang": "python",
            "caption": "KV cache 增量解码，与整段重算结果对拍",
            "content": r'''import math
import torch
import torch.nn.functional as F

def full_attention(q, k, v):
    # 因果注意力整段重算，作为对照基准: q,k,v -> (B, T, D)
    T = q.size(1)
    scores = q @ k.transpose(-2, -1) / math.sqrt(q.size(-1))
    mask = torch.triu(torch.ones(T, T, dtype=torch.bool), diagonal=1)
    scores = scores.masked_fill(mask, float('-inf'))
    return F.softmax(scores, dim=-1) @ v

if __name__ == '__main__':
    torch.manual_seed(0)
    B, T, D = 1, 6, 8
    x = torch.randn(B, T, D)
    Wq, Wk, Wv = torch.randn(D, D) * 0.5, torch.randn(D, D) * 0.5, torch.randn(D, D) * 0.5
    Q, K, V = x @ Wq, x @ Wk, x @ Wv
    ref = full_attention(Q, K, V)

    # 带缓存增量解码：每步只算当前 token 的 q/k/v，历史 K/V 直接拼接复用
    # （增量式天然只看过去，因此基准也必须是 causal 的）
    cache_k = torch.zeros(B, 0, D)
    cache_v = torch.zeros(B, 0, D)
    outs = []
    for t in range(T):
        q_t, k_t, v_t = Q[:, t:t+1], K[:, t:t+1], V[:, t:t+1]     # (B,1,D)
        cache_k = torch.cat([cache_k, k_t], dim=1)   # 新 K 先入 cache
        cache_v = torch.cat([cache_v, v_t], dim=1)
        scores = q_t @ cache_k.transpose(-2, -1) / math.sqrt(D)   # (B,1,t+1)
        outs.append(F.softmax(scores, dim=-1) @ cache_v)
    inc = torch.cat(outs, dim=1)
    assert torch.allclose(ref, inc, atol=1e-5)       # 与整段重算等价
    print('kv cache decode ok')''',
        },
    },

    {
        "id": "handcoded-004",
        "topic": "Attention 手写",
        "type": "手撕",
        "difficulty": 5,
        "frequency": 4,
        "companies": ["字节", "DeepSeek", "月之暗面", "NVIDIA"],
        "years": ["2024", "2025"],
        "question": "写一个 FlashAttention 分块在线 softmax 的简化版（单头即可），说清 online softmax 的 rescale 逻辑。",
        "answerMd": r'''**思路一句话**：把 Q/K/V 分块搬到 SRAM 里算，softmax 不再需要整行——用「运行最大值 m + 运行指数和 l」在线修正：每来一个新块，先把历史累加量按新最大值 rescale，再加上当前块的贡献，最后统一除以 l。

**核心三行**：$m_{new}=\max(m_{old}, \text{rowmax}(S_{ij}))$；$l_{new}=e^{m_{old}-m_{new}}l_{old}+\text{rowsum}(e^{S_{ij}-m_{new}})$；$acc\leftarrow e^{m_{old}-m_{new}}acc + P_{ij}V_{ij}$，最终 `out = acc / l`。acc 保持未归一化是关键，若每块都除会引入二次修正的麻烦。

**易错点**：1）初值 $m=-\infty$，$e^{-\infty-m}=0$ 恰好把空的旧累加清零，不用特判，但要防 $-\infty-(-\infty)=NaN$（本例因果下每行必有可见块）；2）因果块的跳过条件是「k 块起点 > q 块起点」，块内跨界仍要逐位置 mask；3）真实 FlashAttention 还有反向重算（只存 m/l 不存 attn 矩阵）与 kernel 层的 shared memory 排布。

**复杂度**：时间仍 $O(T^2 d)$，但额外显存从 $O(T^2)$ 降到 $O(T)$，HBM 读写从 $O(T^2+Td)$ 降到 $O(T^2 d/M)$（M 为 SRAM 大小）——快在 IO 而非 FLOPs。

**追问**：为什么快（省的是中间矩阵的 HBM 读写）；反向怎么训练（重算 forward 的统计量）；和 KV cache 解码（memory-bound 的另一个场景）关系。''',
        "keyPoints": [
            "分块计算 + 运行统计量 (m, l)，softmax 无需整行",
            "rescale 三行：m_new=max(m_old, rowmax)；l 按指数差缩放累加；acc 未归一化累加",
            "acc 保持未归一化，最后统一除 l，避免反复修正",
            "额外显存 O(T^2)→O(T)，优化的是 HBM IO 而非 FLOPs",
            "因果分块可整块跳过未来 K 块，跨界处逐位置 mask",
        ],
        "followUps": [
            {"q": "FlashAttention 反向传播怎么办？attn 矩阵没存下来。", "a": "前向只保存每个输出行的 m 和 l（O(T)），反向时重新分块计算 S 和 P，用 dO 直接推导 dQ/dK/dV：dV=P^T dO，dQ=P(dO V^T - dO·(P^T V))·缩放等，用重算换取显存，属于典型的「计算换显存」。"},
            {"q": "如果序列长度不是块大小的整数倍怎么办？", "a": "最后一个块直接取剩余长度即可，算法对块大小无要求；工程 kernel 里再处理边界与对齐（padding 到 block 倍数 + mask 掉无效列）。"},
        ],
        "code": {
            "lang": "python",
            "caption": "FlashAttention 分块在线 softmax 简化实现，与 SDPA 对拍",
            "content": r'''import torch
import torch.nn.functional as F

def flash_attention_simplified(q, k, v, bq=2, bk=2, causal=True):
    # q,k,v: (T, D) 单头；演示分块在线 softmax 的核心 rescale 逻辑
    T, D = q.shape
    acc = torch.zeros(T, D)                       # 未归一化输出累加器
    m = torch.full((T,), float('-inf'))           # 每行运行最大值
    l = torch.zeros(T)                            # 每行运行指数和
    for i in range(0, T, bq):
        qi = q[i:i+bq]
        iq = torch.arange(i, i + qi.size(0))
        for j in range(0, T, bk):
            if causal and j >= i + qi.size(0):
                break                             # 整块在未来，直接跳过
            kj, vj = k[j:j+bk], v[j:j+bk]
            s = qi @ kj.T / (D ** 0.5)
            if causal and j + kj.size(0) - 1 > i:
                # 块内含对角线右侧位置：按行加 mask（块尺寸不等时不能省）
                ik = torch.arange(j, j + kj.size(0))
                s = s.masked_fill(ik[None, :] > iq[:, None], float('-inf'))
            m_new = torch.maximum(m[i:i+bq], s.max(dim=-1).values)
            scale = torch.exp(m[i:i+bq] - m_new)              # 旧统计量按新 max 缩放
            p = torch.exp(s - m_new[:, None])                 # 本块未归一化权重
            acc[i:i+bq] = scale[:, None] * acc[i:i+bq] + p @ vj
            l[i:i+bq] = scale * l[i:i+bq] + p.sum(dim=-1)
            m[i:i+bq] = m_new
    return acc / l.clamp_min(1e-12)[:, None]

if __name__ == '__main__':
    torch.manual_seed(0)
    T, D = 7, 16
    q, k, v = torch.randn(T, D), torch.randn(T, D), torch.randn(T, D)
    out = flash_attention_simplified(q, k, v, bq=3, bk=2)
    ref = F.scaled_dot_product_attention(q[None, None], k[None, None], v[None, None], is_causal=True)[0, 0]
    assert torch.allclose(out, ref, atol=1e-5)
    print('flash attention simplified ok')''',
        },
    },

    {
        "id": "handcoded-005",
        "topic": "Attention 手写",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["字节", "阿里", "小米"],
        "years": ["2024", "2025"],
        "question": "手写一个完整的 Transformer Block（Pre-LN：Attention + FFN + 残差），说明为什么现在都用 Pre-LN。",
        "answerMd": r'''**思路一句话**：一个 Block = 两个残差支路：`x = x + Attn(LN(x))`、`x = x + FFN(LN(x))`，LN 放在子层之前叫 Pre-LN，是现代 LLM 的标准结构。

**实现要点**：1）FFN = 两层 Linear 夹激活（GELU 或 SwiGLU），中间维常为 4D（SwiGLU 时约 8/3 D）；2）causal mask 用 bool 上三角传给 attention（True 表示禁止注意）；3）残差是「恒等主路 + 子层支路」，梯度可以无衰减直通底层。

**Pre-LN vs Post-LN**：Post-LN（原始 Transformer）LN 在残差相加之后，深层时梯度需要经过 LN 的归一化操作，容易不稳，必须靠 warmup 撑住；Pre-LN 把 LN 放进支路，主路是恒等映射，梯度更平滑，可以不 warmup 或用很短的 warmup 深堆到上百层。代价是 Pre-LN 顶层表示的「归一化强度」弱一些，通常在最后再加一个 final LN 补上。

**易错点**：两个 LN 不能共用；FFN 的激活别忘（GELU 而不是 ReLU 更常见）；mask 的 True/False 语义（nn.MultiheadAttention 中 True=禁止注意，而 additive mask 是加到 logits 上）。

**复杂度**：单 Block 参数量 ≈ $12D^2$（attn $4D^2$ + FFN $8D^2$），计算量 ≈ $2T\cdot 12D^2$ 前向。''',
        "keyPoints": [
            "两个残差支路：x + Attn(LN(x))、x + FFN(LN(x))",
            "Pre-LN 主路恒等、梯度平滑，深层可稳定训练；Post-LN 依赖 warmup",
            "Pre-LN 末尾通常补一个 final LayerNorm",
            "FFN 中间维 4D（SwiGLU 约 8/3 D），参数量每层约 12D^2",
            "nn.MultiheadAttention 的 bool mask 语义：True 表示禁止注意",
        ],
        "followUps": [
            {"q": "为什么 Pre-LN 深层训练更稳？", "a": "残差主路是恒等映射，反向梯度可以不经过任何归一化/线性变换直达底层；Post-LN 中梯度要穿过 LN 与残差相加点，层数一深初始阶段容易放大失稳，需要 warmup 抑制早期大步长。"},
            {"q": "FFN 用 SwiGLU 时参数量怎么对齐 4D？", "a": "SwiGLU 有三个矩阵（gate/value/up + down），把中间维取约 2/3·4D = 8/3 D，总参数 3·D·(8/3 D) = 8D^2，与普通两层 FFN 的 8D^2 一致；实际常再把 8/3 D 向上取到 256 的倍数利于 kernel。"},
        ],
        "code": {
            "lang": "python",
            "caption": "Pre-LN Transformer Block 组装与形状自检",
            "content": r'''import torch
from torch import nn

class TransformerBlock(nn.Module):
    def __init__(self, d_model, n_heads, ffn_mult=4, dropout=0.0):
        super().__init__()
        self.ln1 = nn.LayerNorm(d_model)
        self.attn = nn.MultiheadAttention(d_model, n_heads, dropout=dropout, batch_first=True)
        self.ln2 = nn.LayerNorm(d_model)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, ffn_mult * d_model),
            nn.GELU(),
            nn.Linear(ffn_mult * d_model, d_model),
            nn.Dropout(dropout),
        )

    def forward(self, x, causal_mask=None):
        # causal_mask: (T, T) bool，True 表示禁止注意的位置
        h = self.ln1(x)
        a, _ = self.attn(h, h, h, attn_mask=causal_mask, need_weights=False)
        x = x + a                              # 残差 1
        x = x + self.ffn(self.ln2(x))          # 残差 2
        return x

def build_causal_mask(T, device='cpu'):
    return torch.triu(torch.ones(T, T, dtype=torch.bool, device=device), 1)

if __name__ == '__main__':
    torch.manual_seed(0)
    B, T, D = 2, 6, 32
    blk = TransformerBlock(D, n_heads=4)
    x = torch.randn(B, T, D)
    out = blk(x, causal_mask=build_causal_mask(T))
    assert out.shape == x.shape and torch.isfinite(out).all()
    assert sum(p.numel() for p in blk.parameters()) > 12 * D * D   # 参数量约 12D^2 量级
    print('transformer block ok')''',
        },
    },

    # ---------------------------------------------------------------- 位置与结构组件
    {
        "id": "handcoded-006",
        "topic": "位置与结构组件",
        "type": "手撕",
        "difficulty": 2,
        "frequency": 3,
        "companies": ["字节", "百度", "腾讯"],
        "years": ["2024", "2025"],
        "question": "手写 Transformer 的 sinusoidal 正弦位置编码，并验证它「能表达相对位置」的性质。",
        "answerMd": r'''**思路一句话**：偶数维放 $\sin(pos/10000^{2i/d})$、奇数维放对应的 $\cos$，每个维度是一段不同波长的正弦波，拼起来给每个位置一个唯一且可泛化到训练未见长度的「指纹」。

**实现要点**：波长从 $2\pi$ 到 $10000\cdot 2\pi$ 几何级数分布，短波长区分近处位置、长波长区分远处位置；实现时用 `torch.exp(arange(0,d,2) * (-log(10000)/d))` 一次性算出所有频率，避免直接算 $10000^{2i/d}$ 上溢。

**关键性质（面试常考）**：1）$PE_{pos+k}$ 可以写成 $PE_{pos}$ 的线性变换（旋转矩阵，正弦和角公式），所以模型能通过线性层学到「相对位置」关系；2）任意两个位置的编码内积只依赖于相对偏移 $k$ 的周期函数；3）每一行的模长恒为 $\sqrt{d/2}$（sin+cos 成对，单位向量），不改变 token embedding 的整体尺度太多；4）pos=0 全零。

**易错点**：`arange(0, d, 2)` 已经是偶数下标，指数里别再写 2i；`pe[:, 0::2]` 与 `pe[:, 1::2]` 的切片别写反；float 精度问题在超长序列（1M+）下明显，会有重复/坍缩风险。

**追问**：为什么有了 sinusoidal 还要学出来的绝对位置编码（可学习 PE 更灵活但泛化到更长序列差）？相对位置编码（T5 bias / RoPE）为什么逐步取代绝对编码。''',
        "keyPoints": [
            "偶数维 sin、奇数维 cos，频率 10000^(-2i/d) 几何级数",
            "PE(pos+k) 是 PE(pos) 的线性变换（正弦和角公式），可表达相对位置",
            "每行模长恒为 sqrt(d/2)，位置向量之间通过旋转区分",
            "实现用 exp(-2i/d·ln10000) 算频率，避免大数上溢",
            "超长序列下低精度正弦编码区分度下降",
        ],
        "followUps": [
            {"q": "sinusoidal 编码和可学习位置编码怎么选？", "a": "可学习 PE 在固定长度任务上通常略好（多一层自由度）；sinusoidal 无参数且可外推到训练长度之外。BERT 用可学习，原始 Transformer 用 sinusoidal；当前主流 LLM 已改用 RoPE 这类旋转相对编码，兼得表达力与外推性。"},
            {"q": "为什么正弦编码能表达相对位置？", "a": "由和角公式 sin(m+k) = sin m cos k + cos m sin k，PE(m+k) 的每个 2i/2i+1 维对等于 [sin mθ, cos mθ] 乘上一个只依赖 k 的 2×2 旋转矩阵。所以任意固定偏移 k 下，两个位置编码之间只差一个与绝对位置无关的线性变换。"},
        ],
        "code": {
            "lang": "python",
            "caption": "sinusoidal 位置编码 + 相对位置性质自检",
            "content": r'''import math
import torch

def sinusoidal_pe(max_len, d_model):
    pe = torch.zeros(max_len, d_model)
    pos = torch.arange(max_len).float().unsqueeze(1)              # (T, 1)
    div = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
    pe[:, 0::2] = torch.sin(pos * div)       # 偶数维 sin
    pe[:, 1::2] = torch.cos(pos * div)       # 奇数维 cos
    return pe

if __name__ == '__main__':
    T, D = 64, 32
    pe = sinusoidal_pe(T, D)
    assert pe.shape == (T, D)
    assert torch.all(pe[0, 0::2] == 0) and torch.all(pe[0, 1::2] == 1)   # pos=0: sin0=0, cos0=1
    assert pe.abs().max() <= 1.0                                  # 取值范围 [-1, 1]
    norms = pe.norm(dim=-1)
    assert torch.allclose(norms, torch.full((T,), math.sqrt(D / 2)), atol=1e-4)  # 模长恒定
    # 相对位置性质：内积只依赖偏移
    dots = pe @ pe.T
    assert abs(dots[3, 7].item() - dots[10, 14].item()) < 1e-4    # 偏移都是 4
    print('sinusoidal pe ok')''',
        },
    },

    {
        "id": "handcoded-007",
        "topic": "位置与结构组件",
        "type": "手撕",
        "difficulty": 4,
        "frequency": 5,
        "companies": ["字节", "智谱", "DeepSeek", "面壁智能"],
        "years": ["2024", "2025"],
        "question": "手写 RoPE 旋转位置编码，并验证注意力分数只依赖相对位置（m−n 不变性）。",
        "answerMd": r'''**思路一句话**：把 q/k 的相邻两维当成二维平面坐标，在位置 m 处旋转 $m\theta$ 角度。内积 $(R_m q)^\top(R_n k)=q^\top R_{n-m} k$ 只依赖相对偏移，天然注入相对位置信息。

**实现要点**：1）频率 $\theta_i = base^{-2i/d}$，同 sinusoidal 的几何级数；2）两两一组做旋转：$(x_{2i}, x_{2i+1}) \to (x_{2i}\cos m\theta_i - x_{2i+1}\sin m\theta_i,\ x_{2i}\sin m\theta_i + x_{2i+1}\cos m\theta_i)$；3）只旋转 Q 和 K，不旋转 V；4）预计算 cos/sin 表，decode 时按当前绝对位置索引。

**易错点**：LLaMA 系实现把张量 reshape 成 `(…, d/2, 2)` 用复数/interleave 方式旋转，与「隔维取偶奇」等价但别混用导致错位；旋转作用在 d_head 维（每头独立）而不是 d_model 维；RoPE 外推靠 NTK/position interpolation 调 base，而不是直接硬撑。

**复杂度**：预计算 $O(T d/2)$，应用旋转逐元素 $O(T d)$，不增加渐近复杂度；KV cache 存的是旋转后的 K。

**性质自检**：同一段序列整体右移后，attention 分数矩阵对应子块应完全一致（代码里验证）；每个 token 旋转后模长不变。''',
        "keyPoints": [
            "两两一组旋转，频率 theta_i = base^(-2i/d_head)",
            "只作用 Q/K 不作用 V，内积只依赖 m-n 实现相对位置",
            "decode 时按绝对位置索引预计算的 cos/sin 表",
            "旋转保持向量模长不变，可作用于 bf16 前先转 fp32 更稳",
            "长上下文外推靠调 base（NTK）或位置插值，而非直接截断",
        ],
        "followUps": [
            {"q": "RoPE 为什么比可学习绝对位置编码更适合长文本？", "a": "绝对 PE 表是有限长查找表，超出训练长度无值；RoPE 是连续函数，配合 base 缩放（NTK-aware、YaRN、位置插值）可以把训练 4K 的模型平滑扩到 128K+，且相对位置性让「平移不变」的注意力结构天然成立。"},
            {"q": "RoPE 加在 Q/K 上，那 GQA 的共享 K 要旋转几次？", "a": "KV cache 里存的应是旋转后的 K，每个 KV 头只需按自己的头维度旋转一次，被多个 Q 头共享时不再重复计算；注意 RoPE 的旋转发生在 attention 计算前，而不是 cache 读取时。"},
        ],
        "code": {
            "lang": "python",
            "caption": "RoPE 实现与相对位置不变性验证",
            "content": r'''import torch

def rope_cos_sin(seq_len, d_head, base=10000.0):
    assert d_head % 2 == 0
    inv_freq = 1.0 / (base ** (torch.arange(0, d_head, 2).float() / d_head))  # theta_i
    t = torch.arange(seq_len).float()
    freqs = torch.outer(t, inv_freq)                    # (T, D/2) 相位 m*theta
    return freqs.cos(), freqs.sin()

def apply_rope(x, cos, sin):
    # x: (B, T, H, D)，偶奇通道两两一组旋转
    cos = cos[None, :, None, :]                         # (1, T, 1, D/2)
    sin = sin[None, :, None, :]
    x1, x2 = x[..., 0::2], x[..., 1::2]
    out = torch.empty_like(x)
    out[..., 0::2] = x1 * cos - x2 * sin
    out[..., 1::2] = x1 * sin + x2 * cos
    return out

def rope_attention(q, k, v, cos, sin):
    # q,k,v: (B, T, H, D)，先旋转 Q/K 再做 attention
    q, k = apply_rope(q, cos, sin), apply_rope(k, cos, sin)
    q, k, v = (t.permute(0, 2, 1, 3) for t in (q, k, v))   # (B, H, T, D)
    scores = q @ k.transpose(-2, -1) / (q.size(-1) ** 0.5)
    return scores.softmax(-1) @ v

if __name__ == '__main__':
    torch.manual_seed(0)
    B, T, H, D = 1, 8, 2, 16
    cos, sin = rope_cos_sin(T, D)
    q, k, v = torch.randn(B, T, H, D), torch.randn(B, T, H, D), torch.randn(B, T, H, D)
    out = rope_attention(q, k, v, cos, sin)
    assert out.shape == (B, H, T, D)
    x = torch.randn(B, T, H, D)
    assert torch.allclose(apply_rope(x, cos, sin).norm(dim=-1), x.norm(dim=-1), atol=1e-4)

    def rope_scores(qq, kk, c, s):       # 只取 logits，验证相对位置不变性
        qq, kk = apply_rope(qq, c, s), apply_rope(kk, c, s)
        qq, kk = qq.permute(0, 2, 1, 3), kk.permute(0, 2, 1, 3)
        return qq @ kk.transpose(-2, -1) / (qq.size(-1) ** 0.5)
    S1 = rope_scores(q, k, cos, sin)[0, 0]                        # (T, T)
    S2 = rope_scores(q[:, 2:], k[:, 2:], cos[:T - 2], sin[:T - 2])[0, 0]
    assert torch.allclose(S1[2:, 2:], S2, atol=1e-5)              # 平移后子块一致
    print('rope ok')''',
        },
    },

    {
        "id": "handcoded-008",
        "topic": "位置与结构组件",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["字节", "阿里", "华为"],
        "years": ["2024", "2025"],
        "question": "手写 LayerNorm 的前向和解析反向（自定义 autograd Function），并与 nn.LayerNorm 对拍梯度。",
        "answerMd": r'''**思路一句话**：LayerNorm 沿最后一维做 $(x-\mu)/\sqrt{\sigma^2+\epsilon}\cdot\gamma+\beta$；反向的核心是「归一化操作本身对 x 的梯度」，因为 $\mu,\sigma$ 都依赖 x，不能只乘 $1/\sigma$。

**反向公式**（设 $g=\partial L/\partial \hat x = \partial L/\partial y \cdot \gamma$，按最后一维）：

$$\frac{\partial L}{\partial x}=\frac{1}{\sigma}\left(g-\text{mean}(g)-\hat x\cdot\text{mean}(g\cdot\hat x)\right)$$

直观理解三项：主项、对均值漂移的修正、对方差漂移的修正（后两项正是一堆样本在「互相拉扯」）。参数梯度：$\partial L/\partial\gamma=\sum g\hat x$，$\partial L/\partial\beta=\sum g$（对 batch/token 维求和）。

**易错点**：方差用有偏估计（`unbiased=False`，除 N 不是 N-1，与 PyTorch 一致）；`var` 别用 `std().pow(2)` 混入无偏修正；mean/var 都要 keepdim；eps 在开根号内。输入是 3D `(B,T,D)` 时求和/求均值的维度要改为对除最后一维外的所有维求和（广播时 torch 自动处理逐元素项，但 dgamma/dbeta 的 reduce 维要写对）。

**复杂度**：前向 $O(N\cdot d)$，反向同阶，可完全 fuse 成一个 kernel（apex/fused layernorm 就是干这个）。

**追问**：LN 为什么按特征维而不是 batch 维（变长序列 batch 统计不稳定、且推理时没有 batch）；LN/BN/RMSNorm/GroupNorm 的适用场景对比。''',
        "keyPoints": [
            "反向必须考虑 mu/var 对 x 的依赖，不能只乘 1/sigma",
            "dx = (1/sigma)·(g − mean(g) − xhat·mean(g·xhat))，逐 last-dim",
            "dgamma = Σ g·xhat，dbeta = Σ g（batch/token 维求和）",
            "方差用有偏估计 unbiased=False，与 PyTorch 对齐",
            "前向可 fuse，统计量只在最后一维内计算",
        ],
        "followUps": [
            {"q": "LN 和 BN 在 NLP 里为什么选 LN？", "a": "序列长度可变、batch 内句子分布差异大，BN 的跨 batch 统计量噪声大且推理时还要维护 running stats；LN 在单个 token 的特征维内归一化，与 batch 无关，训练推理行为一致。CNN 里空间位置共享统计量，BN 才有优势。"},
            {"q": "为什么需要最后一项 −xhat·mean(g·xhat)？", "a": "方差 sigma 也依赖 x，改变某个分量会同时影响 xhat 的所有分量（分母变化）。这一项正是对 sigma 漂移的补偿；若漏掉，数值梯度对拍会系统性偏大，尤其在方差小的通道上。"},
        ],
        "code": {
            "lang": "python",
            "caption": "LayerNorm 前向 + 解析反向（autograd.Function），与官方对拍",
            "content": r'''import torch

class MyLayerNorm(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x, weight, bias, eps=1e-5):
        mu = x.mean(-1, keepdim=True)
        var = x.var(-1, keepdim=True, unbiased=False)      # 有偏方差（除 N）
        sigma_inv = 1.0 / torch.sqrt(var + eps)
        xhat = (x - mu) * sigma_inv
        ctx.save_for_backward(xhat, weight, sigma_inv)
        return xhat * weight + bias

    @staticmethod
    def backward(ctx, grad_out):
        xhat, weight, sigma_inv = ctx.saved_tensors
        g = grad_out * weight                              # dL/dxhat
        # mu 与 var 都依赖 x，需要两项修正；1/sigma 乘在括号外
        dx = sigma_inv * (g - g.mean(-1, keepdim=True)
                          - xhat * (g * xhat).mean(-1, keepdim=True))
        dgamma = (grad_out * xhat).sum(0)                  # 对 batch 维求和
        dbeta = grad_out.sum(0)
        return dx, dgamma, dbeta, None

if __name__ == '__main__':
    torch.manual_seed(0)
    x1 = torch.randn(4, 10, requires_grad=True)
    x2 = x1.detach().clone().requires_grad_(True)
    ln = torch.nn.LayerNorm(10)
    y1 = ln(x1)
    y1.sum().backward()
    w, b = ln.weight.detach(), ln.bias.detach()
    MyLayerNorm.apply(x2, w, b).sum().backward()
    assert torch.allclose(y1, ln(x1).detach())             # 前向与官方一致
    assert torch.allclose(x1.grad, x2.grad, atol=1e-5)     # 输入梯度对拍
    print('layer norm fwd+bwd ok')''',
        },
    },

    {
        "id": "handcoded-009",
        "topic": "位置与结构组件",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 5,
        "companies": ["DeepSeek", "月之暗面", "面壁智能", "字节"],
        "years": ["2024", "2025"],
        "question": "手写 RMSNorm（LLaMA 系标准归一化），说明它和 LayerNorm 的区别与混合精度下的注意点。",
        "answerMd": r'''**思路一句话**：RMSNorm = LayerNorm 去掉中心化和 bias，只做 $y = \frac{x}{\text{RMS}(x)}\cdot\gamma$，$\text{RMS}(x)=\sqrt{\text{mean}(x^2)+\epsilon}$。

**为什么能省**：少一次 mean 归约和一整个 bias 向量，kernel 更省带宽；LLaMA/Qwen/DeepSeek 等主流模型全线使用，效果与 LN 基本持平——因为归一化的主要收益来自「把向量拉回单位球面、稳定各层尺度」，中心化只是锦上添花。

**易错点**：1）统计量计算要提升到 fp32：bf16 下 $x^2$ 容易下溢/上溢（平方会放大动态范围），先 `x.float()` 再 rsqrt，最后转回原 dtype；2）eps 加在 RMS 里（根号内），不是根号外；3）可学习参数只有 $\gamma$ 一个（形状 (d,)），没有 bias；4）PyTorch 2.4+ 有 `nn.RMSNorm` 可对拍。

**等价关系自查**：把输入先减去均值（零均值化）后，RMSNorm 与 LayerNorm（bias=0）输出完全一致——代码里用这个性质验证实现正确性。

**复杂度**：比 LN 少约 1/3 的归约与带宽；反向同样只需处理「除以 RMS」一项修正，比 LN 的反向更简单。

**追问**：为什么 bf16 训练统计量要用 fp32；QK-Norm 是在做什么（对 Q/K 再做 RMSNorm 稳定 attention logits）。''',
        "keyPoints": [
            "y = x / sqrt(mean(x^2)+eps) * gamma，无中心化无 bias",
            "统计量在 fp32 下算，bf16 平方易溢出，算完再转回原 dtype",
            "eps 在根号内；参数只有 gamma",
            "零均值输入下 RMSNorm 与 LayerNorm(bias=0) 等价，可用于自检",
            "比 LN 省一次 mean 归约和一份 bias，带宽更省",
        ],
        "followUps": [
            {"q": "为什么去掉均值中心化影响不大？", "a": "Transformer 各层输入经过残差累加，均值分量本身不大；归一化的主要作用是控制尺度、稳定优化，而不是去除分布偏移。实验上 RMSNorm 与 LN 收敛相当，但计算更省，成为 LLaMA 后的默认选择。"},
            {"q": "RMSNorm 的反向比 LN 简单在哪？", "a": "x 只通过 RMS 进入输出，dx = (gamma/rms)·g − xhat·mean(g·xhat)·(1/d)… 本质上没有均值路径的修正项，只有「尺度」路径，实现和 fuse 都更容易。"},
        ],
        "code": {
            "lang": "python",
            "caption": "RMSNorm（fp32 统计）+ 与 LayerNorm 的等价性自检",
            "content": r'''import torch
from torch import nn

class RMSNorm(nn.Module):
    def __init__(self, d, eps=1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(d))
        self.eps = eps

    def forward(self, x):
        dtype = x.dtype
        x = x.float()                                   # 统计量用 fp32，防 bf16 平方溢出
        rms = torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + self.eps)
        return (x * rms * self.weight.float()).to(dtype)

if __name__ == '__main__':
    torch.manual_seed(0)
    x = torch.randn(2, 5, 8)
    my = RMSNorm(8)
    assert my(x).shape == x.shape and torch.isfinite(my(x)).all()
    # 零均值化后与 LayerNorm(bias=0) 等价
    xc = x - x.mean(-1, keepdim=True)
    ln = nn.LayerNorm(8, elementwise_affine=True)
    with torch.no_grad():
        ln.bias.zero_()
    assert torch.allclose(my(xc), ln(xc), atol=1e-4)
    # bf16 输入也能稳定输出
    xb = torch.randn(2, 5, 8, dtype=torch.bfloat16)
    assert my(xb).dtype == torch.bfloat16 and torch.isfinite(my(xb).float()).all()
    print('rmsnorm ok')''',
        },
    },

    {
        "id": "handcoded-010",
        "topic": "位置与结构组件",
        "type": "手撕",
        "difficulty": 2,
        "frequency": 3,
        "companies": ["智谱", "DeepSeek", "字节"],
        "years": ["2024", "2025"],
        "question": "手写 SwiGLU 前馈层，解释它为什么比普通 FFN 少一次「选维」的纠结、参数量怎么对齐 4D。",
        "answerMd": r'''**思路一句话**：SwiGLU(x) = $W_2(\text{SiLU}(xW_1)\odot xW_3)$：一条 value 支路做线性变换，一条 gate 支路过 SiLU 后当「阀门」逐元素相乘，再投影回 d_model。

**为什么流行**：GLU 类门控让网络能「逐通道决定放行多少」，实验上稳定优于 ReLU/GELU FFN；SiLU(z)=z·sigmoid(z) 处处光滑、有负值区间（比 ReLU 平滑），和门控相乘后表达力更强。LLaMA/Qwen/DeepSeek 的 FFN 全是 SwiGLU。

**参数量账**：普通 FFN 两个矩阵 $D\times 4D + 4D\times D = 8D^2$；SwiGLU 三个矩阵 $3\times D\times d_{ff}$，取 $d_{ff}\approx \frac{8}{3}D$ 才能对齐 $8D^2$。实现上常把 8/3 D 向上取整到 128/256 的倍数（利于 tensor core），所以是「约 8/3」而不是精确值。

**易错点**：三个 Linear 都不带 bias（LLaMA 约定）；gate 和 value 支路别接反（Silu 作用在 gate 上，也有文献反过来，须与预训练权重一致，否则加载权重直接报废）；中间维别默认写 4D。

**复杂度**：FLOPs ≈ $2\times 3TDd_{ff}$ 前向（三次矩阵乘），与普通 FFN 同量级。

**追问**：GeGLU/ReGLU 区别（门控激活换成 GELU/ReLU）；为什么门控有效（乘法交互提供数据依赖的稀疏性）。''',
        "keyPoints": [
            "SwiGLU = W2( SiLU(xW1) ⊙ xW3 )，gate 支路提供数据依赖的权重",
            "三个无 bias Linear，中间维约 8/3 D 对齐 8D^2 参数量",
            "SiLU(z)=z·sigmoid(z)，光滑且有负区间",
            "gate/value 支路顺序必须与预训练权重一致",
            "中间维向上取整到 128/256 倍数利于 GPU kernel",
        ],
        "followUps": [
            {"q": "门控机制为什么有效？", "a": "逐元素乘法引入了输入依赖的非线性路由：gate 支路可以根据当前 token 决定哪些通道放行，相当于动态稀疏激活；相比静态的「线性+激活」，乘法交互提升了同样参数量下的有效容量，GLU 系列在语言任务上稳定占优。"},
            {"q": "SiLU 相比 ReLU 好在哪？", "a": "处处可导（ReLU 在 0 附近梯度不连续）、有轻微负值响应避免「死神经元」、输出在负端趋于 -0.278 的平滑饱和。SwiGLU 论文实验中 SiLU/Swish 门控与 GeGLU 相当，均优于 ReLU 门控。"},
        ],
        "code": {
            "lang": "python",
            "caption": "SwiGLU 前馈层与参数量对齐自检",
            "content": r'''import torch
from torch import nn
import torch.nn.functional as F

class SwiGLU(nn.Module):
    def __init__(self, d_model, d_ff):
        super().__init__()
        self.w1 = nn.Linear(d_model, d_ff, bias=False)   # gate 支路
        self.w3 = nn.Linear(d_model, d_ff, bias=False)   # value 支路
        self.w2 = nn.Linear(d_ff, d_model, bias=False)   # 投影回 d_model

    def forward(self, x):
        return self.w2(F.silu(self.w1(x)) * self.w3(x))

if __name__ == '__main__':
    torch.manual_seed(0)
    D = 96
    d_ff = int(8 * D / 3 + 127) // 128 * 128            # 8/3 D 向上取到 128 倍数
    ffn = SwiGLU(D, d_ff)
    x = torch.randn(2, 5, D)
    assert ffn(x).shape == x.shape
    assert sum(p.numel() for p in ffn.parameters()) == 3 * D * d_ff
    # silu 数值自查：SiLU(z) = z*sigmoid(z)
    z = torch.tensor([-2.0, 0.0, 2.0])
    assert torch.allclose(F.silu(z), z * torch.sigmoid(z))
    # gate=0 时输出应为 0（门关闭）
    with torch.no_grad():
        ffn.w1.weight.zero_()
    assert ffn(x).abs().max() == 0
    print('swiglu ok, d_ff =', d_ff)''',
        },
    },

    {
        "id": "handcoded-011",
        "topic": "位置与结构组件",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 4,
        "companies": ["字节", "月之暗面", "NVIDIA"],
        "years": ["2024", "2025"],
        "question": "手写多头注意力的 reshape 流程，并在其上实现 GQA（分组查询注意力），说明 KV cache 怎么省。",
        "answerMd": r'''**思路一句话**：GQA 让多个 Q 头共享一组 K/V 头：$h_q$ 个 Q 头分组，每 $h_q/h_{kv}$ 个 Q 头共用一个 KV 头，attention 公式不变，只是 K/V 在头维上 repeat 后做普通 MHA。

**实现要点**：1）Q 投影到 $h_q\cdot d$，K/V 投影到 $h_{kv}\cdot d$；2）`repeat_interleave(repeat, dim=1)` 把每个 KV 头复制 repeat 份与 Q 头对齐（Q 头 i 对应 KV 头 i//repeat，与 LLaMA 实现一致）；3）MQA 是 $h_{kv}=1$ 的特例，MHA 是 $h_{kv}=h_q$ 的特例。

**为什么省**：KV cache 大小正比于 $h_{kv}$。LLaMA-2 70B 用 8 个 KV 头 vs 64 个 Q 头，cache 直接缩 8 倍——长上下文/大 batch 推理的显存与带宽瓶颈大幅缓解。质量上 GQA 几乎无损（论文里 MHA≈GQA>MQA），所以成了 7B+ 模型标配。

**易错点**：repeat 的维度是头维（dim=1，B,H,T,D 布局）不是 batch；`repeat_interleave`（逐个复制）与 `repeat`（整块平铺）语义不同，用错会让 Q 头和错误的 KV 头配对；训练时若要从 MHA checkpoint 升级到 GQA，需要对 KV 头做 mean-pooling 转换（uptraining）。

**复杂度**：attention FLOPs 略降（K/V 投影与内积按 $h_{kv}$ 计），decode 显存带宽近似降 $h_q/h_{kv}$ 倍。

**追问**：MQA 为什么质量掉（所有头共享同一 KV 子空间，多样性受损）；GQA 分组数怎么选（8 是质量与 cache 的甜点）。''',
        "keyPoints": [
            "KV 头 repeat_interleave 对齐 Q 头，Q 头 i 对应 KV 头 i // (hq/hkv)",
            "KV cache 与带宽正比 h_kv，GQA 8 头对 64 Q 头可省 8 倍",
            "MQA = h_kv 1 的特例，MHA = h_kv == h_q 特例",
            "repeat_interleave 与 repeat 语义不同，用错会错配头",
            "MHA 权重迁移到 GQA 需 mean-pooling + uptraining",
        ],
        "followUps": [
            {"q": "为什么 8 个 KV 组是常见选择？", "a": "GQA 论文的消融显示 KV 组从 64 降到 8 质量几乎不变、降到 1（MQA）才明显掉点；而 8 组已能把 cache 缩 8 倍，显存与质量在此达到平衡，因此 LLaMA-2 70B、LLaMA-3 全系都用 8。"},
            {"q": "GQA 下 RoPE 怎么加？", "a": "RoPE 按 head 维独立作用：Q 的每个头、K 的每个 KV 头各旋转一次，与是否共享无关；cache 里存旋转后的 K，Q 头共享时直接使用，不需要重复旋转。"},
        ],
        "code": {
            "lang": "python",
            "caption": "GQA 注意力（含 MHA/MQA 特例）与 cache 节省对比",
            "content": r'''import math
import torch
import torch.nn.functional as F

def gqa_attention(q, k, v, n_heads, n_kv_heads, causal=True):
    # q: (B, T, hq*d)，k/v: (B, T, hkv*d)
    B, T, _ = q.shape
    d = q.size(-1) // n_heads
    assert n_heads % n_kv_heads == 0
    q = q.view(B, T, n_heads, d).transpose(1, 2)           # (B, hq, T, d)
    k = k.view(B, T, n_kv_heads, d).transpose(1, 2)
    v = v.view(B, T, n_kv_heads, d).transpose(1, 2)
    repeat = n_heads // n_kv_heads
    if repeat > 1:
        k = k.repeat_interleave(repeat, dim=1)             # Q 头 i 对应 KV 头 i//repeat
        v = v.repeat_interleave(repeat, dim=1)
    scores = q @ k.transpose(-2, -1) / math.sqrt(d)        # (B, hq, T, T)
    if causal:
        m = torch.triu(torch.ones(T, T, dtype=torch.bool, device=q.device), 1)
        scores = scores.masked_fill(m, float('-inf'))
    out = F.softmax(scores, dim=-1) @ v
    return out.transpose(1, 2).reshape(B, T, -1)

if __name__ == '__main__':
    torch.manual_seed(0)
    B, T, d = 2, 5, 16
    for hq, hkv in [(8, 8), (8, 2), (8, 1)]:               # MHA / GQA / MQA
        q = torch.randn(B, T, hq * d)
        k = torch.randn(B, T, hkv * d)
        v = torch.randn(B, T, hkv * d)
        out = gqa_attention(q, k, v, hq, hkv)
        assert out.shape == q.shape
    # 一致性：hkv=hq 时应与普通 MHA 完全一致（repeat=1 分支）
    q = torch.randn(B, T, 8 * d); k = torch.randn(B, T, 8 * d); v = torch.randn(B, T, 8 * d)
    a = gqa_attention(q, k, v, 8, 8)
    b = gqa_attention(q, k, v, 8, 8, causal=False)
    assert not torch.allclose(a, b)                        # causal 与非 causal 必须不同
    print('gqa ok')''',
        },
    },

    # ---------------------------------------------------------------- 解码策略
    {
        "id": "handcoded-012",
        "topic": "解码策略",
        "type": "手撕",
        "difficulty": 2,
        "frequency": 3,
        "companies": ["字节", "美团", "快手"],
        "years": ["2024", "2025"],
        "question": "手写 greedy 解码与 temperature 采样，并用统计实验验证温度对分布形状的影响。",
        "answerMd": r'''**思路一句话**：greedy 是 `argmax` 确定性取最大；temperature 在 softmax 前把 logits 除以 $T$：$p_i \propto e^{z_i/T}$——$T\to 0$ 逼近 greedy，$T\to\infty$ 趋向均匀分布。

**原理**：温度改变 logits 的「锐度」。$T<1$ 拉大 top1 与其余的指数差距，分布更尖、更保守（适合追求准确率）；$T>1$ 压平分布，尾部 token 更多被采到（适合创意写作）。数学上等价于对 softmax 的 logits 做整体缩放，只改变相对陡峭度、不改变排序。

**易错点**：1）$T=0$ 时除零，必须特判为 greedy；2）温度应作用在 logits 上而不是 probabilities 上（先 softmax 再缩放概率是错的，排序虽不变但分布形状不同）；3）数值上大 logits 除以小 $T$ 会溢出，softmax 内部要先减 max；4）temperature 与 top-p 组合时先后顺序会影响结果（先 T 后 top-p 更常见）。

**复杂度**：softmax $O(V)$，multinomial 采样 $O(V)$（或采 prefix-sum $O(\log V)$），greedy $O(V)$。

**追问**：min_p 采样思路（动态阈值 = 最大概率 × 系数）；温度采样和人类偏好对齐的关系（为何 RLHF 后高温可适当调低）。''',
        "keyPoints": [
            "温度除在 logits 上再 softmax，只改变分布陡峭度不改变排序",
            "T→0 等价 greedy，需特判除零",
            "T<1 更确定、T>1 更发散，写代码时先减 max 防溢出",
            "与 top-k/top-p 的组合顺序影响最终分布",
            "采样 O(V)，可用前缀和+二分降到 O(logV)",
        ],
        "followUps": [
            {"q": "temperature 作用在概率上而不是 logits 上会怎样？", "a": "对概率做 p^(1/T) 再归一化在数学上其实等价（幂次与 exp/T 同构），但常见错误是直接线性缩放概率或忘记归一化。正确实现永远是在 logits 上除 T，数值稳定且语义清晰。"},
            {"q": "为什么 chat 模型常用 T≈0.7 而分类模型直接 greedy？", "a": "分类/抽取类任务答案唯一，随机性只有害处；开放式生成需要多样性避免重复模板，T≈0.6~0.9 配合 top-p≈0.9~0.95 在质量与多样性间平衡。"},
        ],
        "code": {
            "lang": "python",
            "caption": "greedy + temperature 采样与分布形状统计验证",
            "content": r'''import torch

def greedy(logits):
    return logits.argmax(dim=-1)                     # 确定性取最大

def sample_with_temperature(logits, temperature=1.0):
    if temperature <= 0:                             # T=0 特判为贪心
        return greedy(logits)
    probs = torch.softmax(logits / temperature, dim=-1)
    return torch.multinomial(probs, num_samples=1).squeeze(-1)

if __name__ == '__main__':
    torch.manual_seed(0)
    logits = torch.tensor([[2.0, 1.0, 0.5, 0.1]])
    assert greedy(logits).item() == 0
    samples = torch.tensor([sample_with_temperature(logits, 0.1) for _ in range(2000)])
    frac0 = (samples == 0).float().mean()
    assert frac0 > 0.95, frac0                       # 低温：几乎总是 top1
    samples = torch.tensor([sample_with_temperature(logits, 5.0) for _ in range(4000)])
    frac3 = (samples == 3).float().mean()
    assert frac3 > 0.05, frac3                       # 高温：尾部 token 也常被采到
    print('temperature ok, T=0.1 p(top1)=%.3f, T=5 p(tail)=%.3f' % (frac0, frac3))''',
        },
    },

    {
        "id": "handcoded-013",
        "topic": "解码策略",
        "type": "手撕",
        "difficulty": 2,
        "frequency": 4,
        "companies": ["字节", "阿里", "百度"],
        "years": ["2024", "2025"],
        "question": "手写 top-k 采样：保留 logits 最高的 k 个 token，其余屏蔽后归一化采样。",
        "answerMd": r'''**思路一句话**：把第 k 大以外的 logits 全部置 $-\infty$，softmax 后它们概率为 0，再在剩下的 k 个里按原比例采样——把长尾噪声一刀切掉。

**实现要点**：1）阈值取「第 k 大的值」：`torch.topk(logits, k).values[..., -1]`，注意并列值会被一起保留（>= 阈值），实际保留数可能 > k，两种约定都可，说清楚即可；2）k=1 退化为 greedy，k≥vocab 等价于纯采样；3）置 $-\infty$ 用 `masked_fill`，softmax 内部自然处理。

**易错点**：1）k 是静态超参的缺陷：分布陡时截太多、分布平时截太少（这正是 top-p 要解决的）；2）对已经过温度缩放的 logits 做还是先做 top-k 再缩放，顺序要与推理框架一致；3）batch 场景下每行阈值不同，topk 要按行（dim=-1）。

**复杂度**：topk $O(V\log k)$（维持大小 k 的堆）或全排序 $O(V\log V)$，softmax $O(V)$。

**追问**：top-k 和 top-p 各自解决什么（k 固定集合大小 vs p 固定概率质量）；min_p 如何同时自适应两者。''',
        "keyPoints": [
            "阈值 = 第 k 大的 logit，低于阈值置 -inf 后再 softmax",
            "并列阈值会被同时保留，需与面试官说明约定",
            "k=1 等价 greedy，k=V 等价纯 temperature 采样",
            "静态 k 无法自适应分布陡峭度，top-p 是其改进",
            "topk 按 dim=-1 逐行做，batch 下每行阈值不同",
        ],
        "followUps": [
            {"q": "top-k 为什么在分布平坦时不好用？", "a": "模型不确定时概率质量分散在几百个 token 上，固定 k 可能只截到 30% 的概率质量，采样几乎随机；反之分布尖锐时 k=50 可能全部冗余。top-p 按累计概率截断能自适应这两种情况。"},
        ],
        "code": {
            "lang": "python",
            "caption": "top-k 过滤 + 采样，验证采样只落在 top-k 内",
            "content": r'''import torch

def top_k_filter(logits, k):
    # logits: (B, V)；只保留每行最大的 k 个，其余置 -inf
    if k <= 0 or k >= logits.size(-1):
        return logits
    thresh = torch.topk(logits, k, dim=-1).values[..., -1:]     # 每行第 k 大
    return logits.masked_fill(logits < thresh, float('-inf'))

def top_k_sample(logits, k, temperature=1.0):
    logits = top_k_filter(logits, k)
    probs = torch.softmax(logits / temperature, dim=-1)
    return torch.multinomial(probs, 1).squeeze(-1)

if __name__ == '__main__':
    torch.manual_seed(0)
    logits = torch.tensor([[3.0, 2.5, 1.0, 0.1, -2.0]])
    filtered = top_k_filter(logits, 2)
    assert filtered[0, :2].tolist() == [3.0, 2.5]
    assert filtered[0, 2:].eq(float('-inf')).all()
    picks = {top_k_sample(logits, 2).item() for _ in range(500)}
    assert picks.issubset({0, 1}), picks               # 只可能落在 top-k
    assert top_k_sample(logits, 1).item() == 0         # k=1 退化为 greedy
    assert top_k_filter(logits, 99).equal(logits)      # k 超界原样返回
    print('top-k ok')''',
        },
    },

    {
        "id": "handcoded-014",
        "topic": "解码策略",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 5,
        "companies": ["字节", "阿里", "快手", "小红书"],
        "years": ["2024", "2025"],
        "question": "手写 top-p（nucleus）采样：保留累计概率达到 p 的最小前缀集合。",
        "answerMd": r'''**思路一句话**：按概率从大到小排序、累加，保留「累计概率首次达到 p」的最小 token 集合，其余置 $-\infty$ 后采样——动态决定候选数：分布尖时候选少，分布平时候选多。

**实现要点**：1）softmax 得概率 → `sort(descending=True)` → `cumsum`；2）截断判断有两种等价写法：`cum > p` 再强制保留第一个（top1 永远保留），或 `cum - p_shift > p`（本 token 之前的累计已超 p 才砍）；3）mask 要用 `scatter_` 把「保留标记」按排序前的原始索引写回，再 masked_fill；4）至少保留 top-1，防止 p 极小时候选集为空。

**易错点**：1）忘记 scatter 回原索引，直接对 sorted 后的 logits 采样（索引对不上原词表）；2）浮点误差：累计和最后一位可能是 0.9999999，p=1.0 时边界抖动，稳妥做法是保证 top1 恒保留；3）与温度的顺序：先温度缩放再 softmax 再 top-p（主流框架如此）。

**复杂度**：排序 $O(V\log V)$，可用 partial sort / 双调排序优化到 $O(V)$ 量级；cumsum 与 scatter 均 $O(V)$。

**追问**：top-p=0.9 时候选集合大小和分布形状的关系；min_p（阈值 = p_max × 系数）与 top-p 的差异；为什么工程上常 k、p、T 叠着用。''',
        "keyPoints": [
            "按概率降序排序后 cumsum，保留累计达到 p 的最小前缀",
            "top-1 必须保留，防止空候选集",
            "mask 需 scatter_ 回原始词表索引再 -inf",
            "动态候选数是相对 top-k 的核心优势",
            "主流顺序：温度缩放 → softmax → top-p 截断 → 采样",
        ],
        "followUps": [
            {"q": "top-p 在极端 p=0.05 时会发生什么？", "a": "几乎只保留 top-1（因为 top1 概率通常已 > 5%），行为接近 greedy；这也说明 top-p 自适应：模型笃定时它不添乱，模型犹豫时它保留足够多的尾部。"},
            {"q": "min_p 和 top-p 有什么本质区别？", "a": "top-p 是全局累计概率视角，候选数随分布自适应但对「相对顶尖 token 的差距」不敏感；min_p 设阈值 = 最大概率 × m（如 0.1），直接砍掉与顶尖差一个量级的 token，在高温下更稳，近年成为社区常用组合。"},
        ],
        "code": {
            "lang": "python",
            "caption": "top-p（nucleus）过滤 + 采样",
            "content": r'''import torch

def top_p_filter(logits, p):
    probs = torch.softmax(logits, dim=-1)
    sorted_probs, sorted_idx = torch.sort(probs, descending=True, dim=-1)
    cum = sorted_probs.cumsum(dim=-1)
    cutoff = cum > p                       # 累计超过 p 的位置全砍
    cutoff[..., 0] = False                 # 至少保留 top-1
    keep_sorted = ~cutoff
    mask = torch.zeros_like(probs, dtype=torch.bool)
    mask.scatter_(-1, sorted_idx, keep_sorted)   # 写回原始索引
    return logits.masked_fill(~mask, float('-inf'))

def top_p_sample(logits, p, temperature=1.0):
    logits = top_p_filter(logits, p) / temperature
    return torch.multinomial(torch.softmax(logits, dim=-1), 1).squeeze(-1)

if __name__ == '__main__':
    torch.manual_seed(0)
    logits = torch.tensor([[5.0, 4.0, 3.0, 2.0, 1.0]])
    p05 = top_p_filter(logits, 0.5)
    assert p05[0, 0].item() == 5.0 and p05[0, 1:].eq(float('-inf')).all()   # 只留 top1
    picks = {top_p_sample(logits, 0.9).item() for _ in range(500)}
    assert picks.issubset({0, 1, 2}), picks        # top3 累计约 0.956>0.9
    picks = {top_p_sample(logits, 0.99).item() for _ in range(500)}
    assert picks.issubset({0, 1, 2, 3}), picks
    print('top-p ok')''',
        },
    },

    {
        "id": "handcoded-015",
        "topic": "解码策略",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["字节", "腾讯", "MiniMax"],
        "years": ["2024", "2025"],
        "question": "手写 repetition penalty（CTRL 式）与 no-repeat-ngram 屏蔽，说清两者分别治什么。",
        "answerMd": r'''**思路一句话**：repetition penalty 是「软惩罚」：已出现的 token 正 logits 除以 $\alpha$、负 logits 乘以 $\alpha$（$\alpha>1$，CTRL 论文式）；no-repeat-ngram 是「硬禁止」：直接把会复现历史 n-gram 的候选 token logits 置 $-\infty$。

**为什么正负号要区别处理**：logits 过 softmax 后只有相对大小有意义。对正数除以 $\alpha$、负数乘以 $\alpha$，等价于「按与 0 的距离等比例压低」，统一用除法会把负 logits 的绝对值变大反而鼓励它，这是最经典的实现 bug。

**no-repeat-ngram 实现**：取已生成序列的最后 $n-1$ 个 token 作为前缀，扫描历史中所有出现该前缀的位置，其后继 token 收集为禁用集合，逐个置 $-\infty$。它治「逐词循环」（如 the the the、成句复读），repetition penalty 治「高频词过度复用」，二者常叠加。

**易错点**：1）penalty 只作用于「已生成的集合」（去重后遍历），不要重复施加；2）n=1 等价禁止任何已出现 token，过强需特判；3）in-place 修改 logits 时注意别污染后续 beam 分支（每个 beam 要独立副本）；4）历史长度不足 n-1 时直接跳过。

**复杂度**：penalty $O(|\text{set}|)$；ngram 扫描 $O(T)$/步（可哈希 n-gram 索引到 $O(1)$ 查询）。

**追问**：frequency/presence penalty（OpenAI 风格）与 CTRL 式的区别；为什么 HF 里 generate 的 repetition_penalty 默认 1.0（副作用：伤害代码/诗歌等需要重复 token 的场景）。''',
        "keyPoints": [
            "正 logits 除 α、负 logits 乘 α，统一除法对负值会反向鼓励",
            "no-repeat-ngram：历史中前缀的后继 token 置 -inf 硬禁止",
            "penalty 只对已出现 token 施加一次（用 set 去重）",
            "beam 场景下每个分支要独立 logits 副本，避免 in-place 污染",
            "n=1 过强需特判；历史不足 n-1 直接跳过",
        ],
        "followUps": [
            {"q": "frequency_penalty 和 presence_penalty 的区别？", "a": "presence_penalty：只要出现过就整体加一个常数负偏置（是否出现）；frequency_penalty：按出现次数线性扣分（出现越多扣越多）。两者都是对 logits 做加性调整，与 CTRL 的乘性惩罚相比更线性、更可控。"},
        ],
        "code": {
            "lang": "python",
            "caption": "重复惩罚与 no-repeat-ngram 屏蔽",
            "content": r'''import torch

def repetition_penalty(logits, generated, penalty=1.2):
    # CTRL 式：正 logits 除 penalty，负 logits 乘 penalty
    for t in set(generated):                     # set 去重，避免重复施加
        if logits[t] > 0:
            logits[t] /= penalty
        else:
            logits[t] *= penalty
    return logits

def ban_repeat_ngrams(logits, generated, n):
    # 禁止生成会构成已出现 n-gram 的 token
    assert n >= 2
    if len(generated) < n - 1:
        return logits
    prefix = list(generated[-(n - 1):])
    banned = set()
    for i in range(len(generated) - n + 1):
        if list(generated[i:i + n - 1]) == prefix:
            banned.add(generated[i + n - 1])     # 该前缀的历史后继
    for t in banned:
        logits[t] = float('-inf')
    return logits

if __name__ == '__main__':
    logits = torch.tensor([1.0, 2.0, 0.5])
    out = repetition_penalty(logits.clone(), [1, 1, 2], penalty=2.0)
    assert out[0].item() == 1.0                  # 未出现不受影响
    assert out[1].item() == 1.0 and out[2].item() == 0.25    # 2/2, 0.5/2
    neg = repetition_penalty(torch.tensor([-1.0, 0.0]), [0], penalty=2.0)
    assert neg[0].item() == -2.0                 # 负 logits 乘 penalty 更负
    lg = ban_repeat_ngrams(torch.tensor([0.0, 3.0, 1.0]), [1, 2, 1, 2], n=2)
    assert lg[1].item() == float('-inf')         # 前缀 2 历史上跟过 1，禁 1
    print('rep penalty / ngram ban ok')''',
        },
    },

    {
        "id": "handcoded-016",
        "topic": "解码策略",
        "type": "手撕",
        "difficulty": 4,
        "frequency": 3,
        "companies": ["字节", "月之暗面", "阿里"],
        "years": ["2025"],
        "question": "把重复惩罚、temperature、top-k、top-p 串成一个完整的 sample_next_token 采样管线（推理框架风格）。",
        "answerMd": r'''**思路一句话**：真实推理框架的采样是一个流水线：**改分**（惩罚已生成 token）→ **定标**（temperature 除 logits）→ **限域**（top-k/top-p 截断）→ **归一化采样**，每一步只做一件事、顺序可配置。

**顺序为什么重要**：1）惩罚必须最先做——它基于原始 logits 的正负号，温度缩放会改变符号判断的相对意义；2）top-k 用排序不依赖温度大小，但 top-p 依赖概率分布形状，所以温度缩放要在 top-p 之前；3）greedy（T=0）直接短路返回 argmax，后面的截断都不用做。

**实现要点**：所有过滤都通过 `masked_fill(-inf)` 完成，不要真的删元素（保持词表维度，索引才对得上）；top-p 的「cum - 当前概率 > p」写法一行搞定最小前缀集合；返回 int 时记得 `.item()`。

**易错点**：1）batch 维度与单条逻辑混写（推理框架里这函数通常 batch=1 逐条或向量化整批）；2）in-place 污染调用方的 logits（先 clone）；3）-inf 参与 multinomial 没问题，但全 -inf 会崩，要保证至少一个候选。

**复杂度**：整体 $O(V\log V)$（排序主导），采样 $O(V)$；工程实现里 top-k/top-p 有 fused kernel（如 flashinfer 的 sampling kernel）避免多次全量排序。

**追问**： speculative decoding 里验证阶段的采样约束怎么和这个管线结合；logit processor 在 HF 里的注册机制。''',
        "keyPoints": [
            "流水线顺序：惩罚 → 温度 → top-k → top-p → 采样",
            "惩罚基于原始 logits 符号，必须最先做",
            "T=0 短路返回 argmax，不做截断",
            "所有过滤用 masked_fill(-inf)，不删元素保索引",
            "整体 O(V logV)，工程上有 fused sampling kernel",
        ],
        "followUps": [
            {"q": "为什么 top-p 必须在 temperature 之后？", "a": "top-p 截断的是概率质量分布，而温度直接改变分布形状（T 大则平）。若先 top-p 再升温，升温后原本被砍的 token 概率仍为 0；先升温再 top-p 才能按「真实要采样的分布」决定保留谁。"},
        ],
        "code": {
            "lang": "python",
            "caption": "完整采样管线：惩罚/温度/top-k/top-p 一条龙",
            "content": r'''import torch

def sample_next_token(logits, generated=None, temperature=1.0,
                      top_k=0, top_p=1.0, rep_penalty=1.0):
    # logits: (V,) 一维张量；返回采到的 token id
    logits = logits.clone()                          # 不污染调用方
    if generated and rep_penalty != 1.0:             # 1) 改分：CTRL 式惩罚
        for t in set(generated):
            logits[t] = logits[t] / rep_penalty if logits[t] > 0 else logits[t] * rep_penalty
    if temperature <= 0:                             # 2) 贪心短路
        return int(logits.argmax())
    logits = logits / temperature                    # 3) 定标
    if top_k and top_k < logits.numel():             # 4) 限域 top-k
        thresh = torch.topk(logits, top_k).values[-1]
        logits = logits.masked_fill(logits < thresh, float('-inf'))
    if top_p < 1.0:                                  # 5) 限域 top-p
        probs = torch.softmax(logits, dim=-1)
        sp, si = torch.sort(probs, descending=True)
        keep = (sp.cumsum(-1) - sp) <= top_p         # 前缀和（不含自身）<= p 的都保留
        mask = torch.zeros_like(keep)
        mask[si[keep]] = True
        logits = logits.masked_fill(~mask, float('-inf'))
    return int(torch.multinomial(torch.softmax(logits, dim=-1), 1))

if __name__ == '__main__':
    torch.manual_seed(0)
    lg = torch.tensor([1.0, 4.0, 2.0, 0.5])
    assert sample_next_token(lg, temperature=0) == 1              # 贪心
    assert sample_next_token(lg, generated=[1], rep_penalty=100.0, temperature=0) == 2
    picks = {sample_next_token(lg, top_k=2) for _ in range(300)}  # 只从 top2 采
    assert picks.issubset({1, 2}), picks
    picks = {sample_next_token(torch.tensor([4., 3., 2., 1.]), top_p=0.5) for _ in range(300)}
    assert picks.issubset({0, 1}), picks                          # top1 累计 0.64>0.5
    print('sampling pipeline ok')''',
        },
    },

    {
        "id": "handcoded-017",
        "topic": "解码策略",
        "type": "手撕",
        "difficulty": 4,
        "frequency": 4,
        "companies": ["字节", "百度", "小米"],
        "years": ["2024", "2025"],
        "question": "手写 beam search（支持 EOS 提前结束），并构造一个贪心掉进局部最优、beam size=2 能救回来的例子。",
        "answerMd": r'''**思路一句话**：维护 k 个累计 log 概率最高的候选序列，每步把每个 beam 展开到全词表取全局 top-k，EOS 结束的 beam 移入 finished 列表，最后从 finished（或未结束的兜底）里选全局最优。

**实现主线**：`beams = [([], 0.0)]` 起步；每轮对每个未结束 beam 枚举下一 token 得到 candidates，按「累计 logprob + 长度惩罚」排序取 top-k；已 EOS 的 beam 不再展开、直接进 finished。

**必讲的两个细节**：1）**长度惩罚**：sum-logprob 天然偏向短句（概率连乘越乘越小），主流做法是得分除以 $\text{len}^\alpha$（$\alpha\in[0.6,0.7]$，GNMT 式）或对 EOS 后继续算 logprob 做归一化，否则翻译任务会系统性截短；2）**beam 之间要去重**（同一前缀展开相同 token 会重复计分）。

**与采样的关系**：beam size=1 就是 greedy；beam search 是「确定性搜索最优」而采样是「按分布抽」，机器翻译/结构化生成用 beam，开放对话用采样——现役 chat 模型基本不 beam。

**易错点**：finished 和 alive 分开管理；`float('-inf')` 屏蔽非法 token；对数概率相加不是相乘；构造的反例要真的让贪心错（代码里验证）。

**复杂度**：$O(T\cdot k\cdot V\log(kV))$，比采样贵一个 k·log 因子，是它被在线服务弃用的原因之一。''',
        "keyPoints": [
            "每步全部 beam 展开后取全局 top-k，不是每 beam 各留 1",
            "EOS 结束的 beam 进 finished 不再展开",
            "长度惩罚 len^alpha 修正 sum-logprob 偏短句的偏差",
            "log 概率相加；beam size=1 即 greedy",
            "复杂度 O(T·k·V·log(kV))，在线服务少用",
        ],
        "followUps": [
            {"q": "为什么 chat 模型几乎不用 beam search？", "a": "开放生成没有唯一正确答案，beam 找到的是「高概率模板」，输出保守且雷同；采样（top-p 等）保留多样性更符合对话需求。beam 主要留在翻译、摘要、代码补全等有明确最优解的结构化任务。"},
            {"q": "长度惩罚的 alpha 怎么取？", "a": "GNMT 用 lp = ((5+|y|)/6)^alpha，alpha∈[0.6,0.7]；alpha=0 不惩罚（偏短），alpha=1 平均每 token 概率（偏长）。要按任务输出长度分布调，评测集上扫一遍即可。"},
        ],
        "code": {
            "lang": "python",
            "caption": "beam search + 贪心局部最优反例验证",
            "content": r'''import math

def beam_search(next_logprobs, beam_size, max_len, eos=None):
    # next_logprobs(prefix)->list[float]：下一 token 的 log 概率；eos 结束该 beam
    beams = [([], 0.0)]                              # (序列, 累计 logprob)
    finished = []
    for _ in range(max_len):
        cand = []
        for seq, score in beams:
            if eos is not None and seq and seq[-1] == eos:
                finished.append((seq, score))        # 已结束，直接保留
                continue
            for v, lp in enumerate(next_logprobs(seq)):
                cand.append((seq + [v], score + lp))
        if not cand:
            break
        cand.sort(key=lambda x: x[1], reverse=True)
        beams = cand[:beam_size]                     # 全局 top-k
    finished.extend(beams)                           # 未结束的兜底计入
    finished.sort(key=lambda x: x[1], reverse=True)
    return finished[0]

if __name__ == '__main__':
    # 词表 {0,1}，长度 2；最优路径 (1,0) 首步局部次优
    table = {(): [-0.5, -0.6], (0,): [-0.5, -0.6], (1,): [-0.02, -5.0]}
    lp = lambda seq: table[tuple(seq)]
    seq, score = beam_search(lp, beam_size=2, max_len=2)
    assert tuple(seq) == (1, 0) and abs(score + 0.62) < 1e-6, (seq, score)
    seq1, score1 = beam_search(lp, beam_size=1, max_len=2)       # 贪心掉坑 (0,0)
    assert tuple(seq1) == (0, 0) and score1 < score, (seq1, score1)   # 贪心分更低
    # EOS 提前结束：步 0 结束
    table2 = {(): [-0.1, -3.0], (0,): [0.0, 0.0], (1,): [0.0, 0.0]}
    seq2, _ = beam_search(lambda s: table2[tuple(s)], beam_size=2, max_len=2, eos=0)
    assert tuple(seq2)[:1] == (0,)          # 第一步就 EOS，提前结束被保留
    print('beam search ok, best =', seq, score)''',
        },
    },

    # ---------------------------------------------------------------- Tokenizer
    {
        "id": "handcoded-018",
        "topic": "Tokenizer",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 4,
        "companies": ["字节", "OpenAI", "智谱"],
        "years": ["2024", "2025"],
        "question": "手写简化版 BPE：从语料训练 merge 表，再用 merge 表编码新词，验证 lowest 能切成 low+est。",
        "answerMd": r'''**思路一句话**：BPE 训练就是「从字符级开始，每轮统计全语料中频次最高的相邻符号对，合并成新符号，重复 M 次」；编码则是把 merge 表按训练顺序重放，贪心合并。

**训练主线**：按空格切词统计词频（key 是符号元组，value 是词频，避免重复算长文本）→ 每轮 $O(V\cdot \bar l)$ 统计 pair → 取最大频次 pair（平手用字典序保证确定性）→ 扫描所有词把该 pair 拼成新符号。

**编码主线**：对输入词先拆成字符，按 merge 表顺序逐条尝试合并（顺序即优先级），扫描一遍即可。这也解释了为什么 BPE 编码结果唯一确定。

**易错点**：1）真实 BPE 会在词尾加 `</w>`（或 sentencepiece 的 ▁）标记，防止跨词合并，简版靠「词内切分」规避，面试要说清；2）训练统计要在「合并后的词集合」上做增量更新，朴素全量重扫是 $O(M\cdot V\cdot \bar l)$，HF tokenizers 用优先队列 + 增量更新到 $O(M\log V)$；3）编码时 merge 顺序必须与训练一致，乱序会得到不同的切分；4）中文/多语言要按字节（byte-level BPE，GPT-2 起）保证任意文本可编码。

**复杂度**：训练朴素 $O(MVL)$；编码 $O(M\cdot l)$。词表大小 = 初始字符表 + M。''',
        "keyPoints": [
            "训练：统计最高频相邻 pair → 合并 → 重复 M 次",
            "编码：按训练顺序重放 merge 表，结果确定",
            "词频按词聚合统计，避免长文本重复计算",
            "真实实现有词尾标记/字节级兜底，防跨词与 OOV",
            "HF 用优先队列增量更新，训练 O(M log V)",
        ],
        "followUps": [
            {"q": "byte-level BPE 解决什么问题？", "a": "Unicode 词表爆炸和 OOV：以 256 个字节为初始字符集，任何文本都能编码，不依赖预归一化。GPT-2 起的标准做法；代价是罕见字符/生僻中文会被拆成多个字节 token，效率下降。"},
            {"q": "词表大小怎么权衡？", "a": "词表大 → 序列短（推理快、上下文利用率高）但 embedding 参数大、低频 token 欠训练；常见 LLM 用 32K~256K。经验上 vocab ≈ 数万时 FLOPs 与参数量的平衡最好，扩词表要配合 embedding 初始化与继续训练。"},
        ],
        "code": {
            "lang": "python",
            "caption": "BPE 训练 + 编码（简版），验证 lowest -> low est",
            "content": r'''from collections import Counter

def train_bpe(text, num_merges):
    word_freq = Counter(text.split())
    words = {tuple(w): f for w, f in word_freq.items()}   # 符号元组 -> 词频
    merges = []
    for _ in range(num_merges):
        stats = Counter()
        for sym, f in words.items():
            for a, b in zip(sym, sym[1:]):
                stats[(a, b)] += f
        if not stats:
            break
        best, _ = max(stats.items(), key=lambda kv: (kv[1], kv[0]))   # 平手取字典序
        merges.append(best)
        new_words = {}
        for sym, f in words.items():
            out, i = [], 0
            while i < len(sym):
                if i + 1 < len(sym) and (sym[i], sym[i + 1]) == best:
                    out.append(sym[i] + sym[i + 1])       # 合并成新符号
                    i += 2
                else:
                    out.append(sym[i]); i += 1
            t = tuple(out)
            new_words[t] = new_words.get(t, 0) + f
        words = new_words
    return merges

def bpe_encode(word, merges):
    sym = list(word)
    for a, b in merges:                          # 按训练顺序贪心重放
        i = 0
        while i < len(sym) - 1:
            if sym[i] == a and sym[i + 1] == b:
                sym[i:i + 2] = [a + b]
            else:
                i += 1
    return sym

if __name__ == '__main__':
    text = 'low low low lower lowest lowest low newest newest'
    merges = train_bpe(text, num_merges=6)
    assert bpe_encode('lowest', merges) == ['low', 'est'], bpe_encode('lowest', merges)
    assert bpe_encode('low', merges) == ['low']
    assert bpe_encode('lowest', merges) == bpe_encode('lowest', merges)   # 确定性
    print('bpe ok, merges:', merges[:4], '...')''',
        },
    },

    {
        "id": "handcoded-019",
        "topic": "Tokenizer",
        "type": "手撕",
        "difficulty": 2,
        "frequency": 3,
        "companies": ["百度", "腾讯", "美团"],
        "years": ["2024", "2025"],
        "question": "手写词典 + Trie 的贪心最长匹配分词（正向最大匹配），处理无匹配时的单字兜底。",
        "answerMd": r'''**思路一句话**：从句首开始，每次尝试切出「词典里能命中的最长前缀」，命中则跳到其后继续，否则退化为单字符（UNK 兜底）；Trie 把每次前缀查询做到 $O(\text{词长})$。

**实现主线**：1）建 Trie：逐字符 `setdefault` 下钻，词尾打 `#` 标记，同时记录最大词长 max_len 用于截断尝试范围；2）切分：位置 i 从 `min(max_len, 剩余长度)` 往下试，沿 Trie 走，走到带 `#` 的节点即命中。

**易错点**：1）for-else 结构（循环完整走完没 break 才走 else）处理「无任何命中」的兜底，这是 Pythonic 但易错的写法；2）max_len 不裁剪的话每个位置都要试到底，浪费且可能被超长串卡住；3）贪心最长匹配有歧义缺陷（如「研究生命起源」切成「研究生/命」），可用双向最大匹配或 jieba 的 DAG+动态规划缓解，面试可主动提。

**复杂度**：建 Trie $O(\sum|w|)$；切分 $O(n\cdot \text{max\_len})$（Trie 单次查询 $O(\text{max\_len})$）。相比每步二分哈希集合，Trie 无哈希开销且天然支持前缀剪枝。

**追问**：和 LLM 的 BPE 有什么本质区别（词典是静态先验 vs BPE 从语料统计学出、可编码任意串）；为什么搜索/广告 query 理解还在用词典分词（可控、可注入领域词）。''',
        "keyPoints": [
            "Trie 词尾打 # 标记，记录最大词长裁剪尝试范围",
            "每个位置从最长尝试到最短，命中即切走",
            "无匹配退化为单字符兜底（for-else）",
            "贪心最长匹配有切分歧义，双向匹配/DAG+DP 可缓解",
            "查询 O(max_len)，整体 O(n·max_len)",
        ],
        "followUps": [
            {"q": "正向最大匹配的歧义问题怎么解？", "a": "经典手段是双向最大匹配（正、反各切一遍，结果一致则采纳，不一致用规则/词频裁决）；更严谨的是把所有候选路径建成 DAG，用词频作为一元势函数做 Viterbi，jieba 内部即此方案。"},
        ],
        "code": {
            "lang": "python",
            "caption": "Trie 建库 + 正向最大匹配切分",
            "content": r'''def build_trie(vocab):
    trie, max_len = {}, 1
    for w in vocab:
        node = trie
        for ch in w:
            node = node.setdefault(ch, {})
        node['#'] = True                          # 词结束标记
        max_len = max(max_len, len(w))
    return trie, max_len

def greedy_max_match(text, trie, max_len):
    tokens, i = [], 0
    n = len(text)
    while i < n:
        hit = None
        for l in range(min(max_len, n - i), 0, -1):   # 从最长往下试
            node = trie
            ok = True
            for ch in text[i:i + l]:
                if ch not in node:
                    ok = False
                    break
                node = node[ch]
            if ok and '#' in node:
                hit = text[i:i + l]
                break
        if hit is None:                           # 无命中：单字兜底
            tokens.append(text[i]); i += 1
        else:
            tokens.append(hit); i += len(hit)
    return tokens

if __name__ == '__main__':
    vocab = ['大模型', '模型', '训练', '训练大模型', '我爱', '人工智能']
    trie, ml = build_trie(vocab)
    assert greedy_max_match('我爱人工智能', trie, ml) == ['我爱', '人工智能']
    assert greedy_max_match('训练大模型', trie, ml) == ['训练大模型']   # 最长优先
    assert greedy_max_match('你好X', trie, ml) == ['你', '好', 'X']    # 单字兜底
    print('greedy max match ok')''',
        },
    },

    # ---------------------------------------------------------------- 训练组件
    {
        "id": "handcoded-020",
        "topic": "训练组件",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 5,
        "companies": ["字节", "腾讯", "华为", "美团"],
        "years": ["2024", "2025"],
        "question": "手写数值稳定的 softmax 和交叉熵（含解析梯度），用数值梯度对拍验证。",
        "answerMd": r'''**思路一句话**：softmax 先减行最大值防 exp 上溢；交叉熵直接用 log_softmax（$z-\max-\log\sum e^{z-\max}$）一步算出，梯度为极简的 $(p-\text{onehot})/N$。

**稳定性分析**：$e^{1000}$ 在 fp32 直接溢出成 inf，但减去 max 后最大项变成 $e^0=1$，其余 $\le 1$，永远安全；logsumexp 同理。减 max 不改变 softmax 结果（分子分母同乘 $e^{-\max}$）。

**梯度推导**（必讲）：$L=-\log p_y$，$\partial L/\partial z_i = p_i - \mathbb{1}[i=y]$，mini-batch 上再除 N。这个形式优雅到可以直接写进 kernel（fused softmax-CE），也是所有分类损失（label smoothing、focal loss）的手写基础。

**易错点**：1）对 log(p) 直接取对数而非 log_softmax——p 可能为 0 产生 $-\infty$；2）mean 和 sum 归一化不一致（梯度差 N 倍）；3）gather 目标是 target.unsqueeze(1)；4）数值梯度验证要用中心差分 $(f(x+\epsilon)-f(x-\epsilon))/2\epsilon$，$\epsilon\approx 10^{-5}$，误差 $O(\epsilon^2)$ 量级，对拍通过基本可断定推导无误。

**复杂度**：$O(NV)$ 时间、$O(N)$ 额外空间（不物化概率矩阵时可流式）；大词表用 sampled softmax / hierarchical softmax。生产框架会把 softmax+CE 融合成单个 kernel 一次遍历，省一次概率矩阵的读写带宽，这也是各训练框架都在卷的 fuse 粒度。''',
        "keyPoints": [
            "先减行最大值再 exp，永不溢出",
            "交叉熵用 log_softmax 整链计算，不要 log(softmax 输出)",
            "解析梯度 (p − onehot)/N，简洁且可 fused",
            "数值梯度用中心差分验证，eps 取 1e-5 量级",
            "mean/sum 归一化要与梯度系数一致",
        ],
        "followUps": [
            {"q": "label smoothing 怎么改这个损失？", "a": "目标分布从 onehot 变为 (1−ε)·onehot + ε/K·uniform，梯度变为 p − q（q 是平滑后的目标分布），实现上只需替换 gather 出的目标项并加上 ε/K·Σz 的常数修正项。"},
            {"q": "大词表（100万+）下 softmax-CE 怎么办？", "a": "sampled softmax / NCE（负采样近似）、hierarchical softmax（树结构 logV）、或工程上分块计算 logsumexp 流式降显存。LLM 时代普遍直接全 softmax，因为词表 10 万级可承受，重点在 fuse kernel 省带宽。"},
        ],
        "code": {
            "lang": "python",
            "caption": "数值稳定 softmax/CE（前向 + 解析梯度 + 数值梯度对拍）",
            "content": r'''import numpy as np

def stable_softmax(z):
    z = z - z.max(axis=-1, keepdims=True)        # 减 max 防 exp 上溢
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)

def cross_entropy(logits, y):
    # logits: (N, C)，y: (N,) int；返回 loss 与 dL/dz
    z = logits - logits.max(axis=-1, keepdims=True)
    log_probs = z - np.log(np.exp(z).sum(axis=-1, keepdims=True))   # log_softmax
    n = logits.shape[0]
    loss = -log_probs[np.arange(n), y].mean()
    grad = np.exp(log_probs)
    grad[np.arange(n), y] -= 1.0                 # dL/dz = (p - onehot)/N
    grad /= n
    return loss, grad

if __name__ == '__main__':
    big = np.array([[1000.0, 1000.0, 999.0]])
    p = stable_softmax(big)                      # 不减 max 会溢出成 nan
    assert np.all(np.isfinite(p)) and abs(p.sum() - 1) < 1e-6
    assert abs(p[0, 0] - p[0, 1]) < 1e-6         # 同分同概率
    logits = np.array([[2.0, 1.0, 0.1], [0.5, 2.5, -1.0]])
    y = np.array([0, 1])
    loss, grad = cross_entropy(logits, y)
    eps = 1e-5                                   # 中心差分数值梯度对拍
    for i in range(2):
        for j in range(3):
            lp = logits.copy(); lp[i, j] += eps
            lm = logits.copy(); lm[i, j] -= eps
            num = (cross_entropy(lp, y)[0] - cross_entropy(lm, y)[0]) / (2 * eps)
            assert abs(num - grad[i, j]) < 1e-6, (i, j, num, grad[i, j])
    print('stable softmax/CE ok, loss =', round(loss, 4))''',
        },
    },

    {
        "id": "handcoded-021",
        "topic": "训练组件",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 4,
        "companies": ["字节", "阿里", "拼多多"],
        "years": ["2024", "2025"],
        "question": "手写 Adam 优化器（含偏差修正），与 torch.optim.Adam 在同一目标上迭代对拍。",
        "answerMd": r'''**思路一句话**：Adam = 一阶动量 $m_t$（梯度的指数滑动平均，管方向）+ 二阶动量 $v_t$（平方梯度滑动平均，管步长）+ 偏差修正（补偿 $m_0=v_0=0$ 的冷启动偏小）。

**四个公式**：$m_t=\beta_1 m_{t-1}+(1-\beta_1)g_t$；$v_t=\beta_2 v_{t-1}+(1-\beta_2)g_t^2$；$\hat m=m_t/(1-\beta_1^t)$、$\hat v=v_t/(1-\beta_2^t)$；$\theta\leftarrow\theta-\eta\,\hat m/(\sqrt{\hat v}+\epsilon)$。

**偏差修正为什么必要**：初值 0 使前几步 $m_t\approx(1-\beta_1)\sum\beta_1^{t-i}g_i$，系统性偏小约 $(1-\beta_1^t)$ 倍，不修正则初期步长过小、warmup 变相加倍；修正后初期步长近似为符号梯度 × lr，行为类似「带阻尼的 signSGD」。

**易错点**：1）实现用 in-place（`mul_/addcmul_`）避免每次分配新张量，同时注意梯度清零时机（本例手动 `p.grad=None`）；2）eps 加在 $\sqrt{\hat v}$ 外面（与 PyTorch 一致）；3）$1-\beta^t$ 的 t 从 1 开始计；4）AdamW 的解耦衰减是「更新时直接缩参数」而非把 L2 加进 g。

**复杂度**：每步 $O(P)$ 额外显存（两个状态张量，混合精度训练中是大头，衍生出 8-bit Adam / Adafactor）。

**追问**：β2 调小（0.95）为什么是大模型常见选择（对 loss spike 响应快）；Adam 与 signSGD 的关系。''',
        "keyPoints": [
            "m 管方向、v 管步长、偏差修正补冷启动",
            "更新式 θ −= lr · m̂/(√v̂ + eps)，eps 在根号外",
            "偏差修正因子 1−β^t，t 从 1 起计",
            "状态显存 2×参数量，大模型用 8-bit Adam/Adafactor 降",
            "AdamW 的衰减在更新步直接乘参数，不进梯度",
        ],
        "followUps": [
            {"q": "为什么大模型训练常把 beta2 从 0.999 调到 0.95？", "a": "预训练中梯度分布突变频繁（数据分布切换、loss spike）。0.999 的 v 记忆窗口太长，spike 后步长被长期压小、恢复慢；0.95 窗口短，对突发梯度响应快，训练更稳。GPT-3/LLaMA 均用 0.95。"},
        ],
        "code": {
            "lang": "python",
            "caption": "手写 Adam 与 torch.optim.Adam 逐步对拍",
            "content": r'''import torch

class MyAdam:
    def __init__(self, params, lr=0.01, beta1=0.9, beta2=0.999, eps=1e-8):
        self.params = list(params)
        self.lr, self.b1, self.b2, self.eps = lr, beta1, beta2, eps
        self.m = [torch.zeros_like(p) for p in self.params]
        self.v = [torch.zeros_like(p) for p in self.params]
        self.t = 0

    @torch.no_grad()
    def step(self):
        self.t += 1
        for p, m, v in zip(self.params, self.m, self.v):
            g = p.grad
            m.mul_(self.b1).add_(g, alpha=1 - self.b1)            # 一阶矩
            v.mul_(self.b2).addcmul_(g, g, value=1 - self.b2)     # 二阶矩
            m_hat = m / (1 - self.b1 ** self.t)                   # 偏差修正
            v_hat = v / (1 - self.b2 ** self.t)
            p.add_(m_hat / (v_hat.sqrt() + self.eps), alpha=-self.lr)

if __name__ == '__main__':
    def loss_fn(p):
        return (p[0] - 3) ** 2 + (p[1] + 1) ** 2        # 最优解 (3, -1)
    x1 = torch.nn.Parameter(torch.zeros(2))
    x2 = torch.nn.Parameter(torch.zeros(2))
    o1, o2 = MyAdam([x1], lr=0.05), torch.optim.Adam([x2], lr=0.05)
    for _ in range(300):
        loss_fn(x1).backward(); o1.step(); x1.grad = None
        loss_fn(x2).backward(); o2.step(); x2.grad = None
    assert torch.allclose(x1, x2, atol=1e-6), (x1, x2)   # 与官方逐步一致
    assert (x1 - torch.tensor([3.0, -1.0])).abs().max() < 0.1
    print('adam ok, final =', x1.detach().tolist())''',
        },
    },

    {
        "id": "handcoded-022",
        "topic": "训练组件",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 5,
        "companies": ["阿里", "字节", "MiniMax"],
        "years": ["2024", "2025"],
        "question": "手写 LoRA 线性层：冻结底座、旁路低秩矩阵、支持权重合并推理，验证初始等价与合并一致。",
        "answerMd": r'''**思路一句话**：$y=W_0x+\frac{\alpha}{r}B(Ax)$，$W_0$ 冻结，A 用随机高斯初始化、B 初始化为 0，训练开始时旁路输出为零、与原模型严格等价，只训 $r(m+n)$ 个参数。

**关键设计**：1）**B=0 初始化**：若 A、B 都随机，初始就随机扰动原模型，SFT 起点漂移；2）**scale = α/r**：调 r 时不用重调学习率，α 固定下变化 r 只影响旁路的「相对强度」；3）**合并推理**：$W_0\mathrel{+}= \frac{\alpha}{r}BA$ 后旁路消失，无额外推理延迟，多 LoRA 服务则用 S-LoRA 式 batched 旁路计算。

**易错点**：1）冻结要在优化器构造之前 `requires_grad_(False)`，否则 weight decay 仍会更新；2）A、B 的形状是 (r, in) 和 (out, r)，转置乘法别写错；3）dropout 一般加在旁路输入 x 上（与原论文一致），别加在 BA 输出上；4）合并前 B=0 时合并无效果，测试要先给 A/B 随机值。

**复杂度**：可训练参数从 $mn$ 降到 $r(m+n)$（r≪min(m,n)）；显存省在优化器状态（Adam 的 2×参数量只覆盖旁路）；旁路计算量 $O(T\cdot r(m+n))$。

**追问**：为什么 LoRA 有效（微调的更新量天然低秩）；QLoRA 加了什么（4bit NF4 底座 + 双重量化 + paged optimizer）；DoRA 改了什么。''',
        "keyPoints": [
            "y = W0 x + (α/r)·B(Ax)，A 高斯初始化、B 置 0",
            "B=0 保证训练起点与原模型严格等价",
            "冻结在构造优化器之前做，防 weight decay 泄漏",
            "合并 W0 += (α/r)BA 可消除推理延迟",
            "可训参数 mn → r(m+n)，省的是 Adam 状态显存",
        ],
        "followUps": [
            {"q": "r 取多大合适？", "a": "常见 r=8~64。秩足够表达「任务偏移」即可：风格类任务 r=8 常够，领域知识注入/代码类可到 64~128。r 过大逼近全参微调、过拟合风险与显存开销都上升，α/r 的 scale 记得同步考虑。"},
            {"q": "LoRA 应用到哪些层？", "a": "原论文只放 attention 的 Wq/Wv；实践中 attention 的 QKVO 全放 + MLP 的 gate/up/down 一起效果更好，尤其是知识型任务。全部线性层都挂 LoRA 的显存开销仍远小于全参。"},
        ],
        "code": {
            "lang": "python",
            "caption": "LoRALinear：冻结底座 + 旁路 + merge 推理",
            "content": r'''import torch
from torch import nn

class LoRALinear(nn.Module):
    def __init__(self, in_f, out_f, r=4, alpha=8, dropout=0.0):
        super().__init__()
        self.base = nn.Linear(in_f, out_f, bias=False)
        self.base.weight.requires_grad_(False)          # 冻结底座
        self.lora_A = nn.Parameter(torch.randn(r, in_f) / in_f ** 0.5)
        self.lora_B = nn.Parameter(torch.zeros(out_f, r))   # B=0：起点等价
        self.scale = alpha / r
        self.dropout = nn.Dropout(dropout)
        self.merged = False

    def forward(self, x):
        if self.merged:                     # 已合并：只走底座，防旁路双重计入
            return self.base(x)
        # x: (..., in) -> base + scale * x @ A^T @ B^T
        return self.base(x) + self.scale * (self.dropout(x) @ self.lora_A.T @ self.lora_B.T)

    @torch.no_grad()
    def merge(self):
        if not self.merged:                 # W0 += scale * B@A，合并后置标志
            self.base.weight += self.scale * (self.lora_B @ self.lora_A)
            self.merged = True

if __name__ == '__main__':
    torch.manual_seed(0)
    layer = LoRALinear(16, 32, r=4, alpha=8)
    assert layer.lora_A.numel() + layer.lora_B.numel() == 4 * (16 + 32)   # r(m+n)
    x = torch.randn(2, 5, 16)
    assert torch.allclose(layer(x), layer.base(x))       # B=0 初始严格等价
    layer(x).sum().backward()
    assert layer.base.weight.grad is None                # 底座无梯度
    assert layer.lora_A.grad is not None and layer.lora_B.grad is not None
    with torch.no_grad():                                # 模拟训练后
        layer.lora_A.normal_(0, 0.1); layer.lora_B.normal_(0, 0.1)
    x2 = torch.randn(2, 5, 16)
    y_before = layer(x2)
    layer.merge()
    assert torch.allclose(layer(x2), y_before, atol=1e-4)   # 合并前后一致
    print('lora ok')''',
        },
    },

    {
        "id": "handcoded-023",
        "topic": "训练组件",
        "type": "手撕",
        "difficulty": 4,
        "frequency": 4,
        "companies": ["美团", "快手", "拼多多"],
        "years": ["2024", "2025"],
        "question": "用 numpy 手写两层 MLP（ReLU + softmax）的完整前向传播和反向传播，数值梯度对拍。",
        "answerMd": r'''**思路一句话**：前向 $z_1=XW_1+b_1 \to a_1=\text{ReLU}(z_1) \to z_2=a_1W_2+b_2 \to p=\text{softmax}(z_2)$；反向从 $\partial L/\partial z_2=(p-\text{onehot})/N$ 出发，按计算图用链式法则逐层回传。

**反向四步**：1）$\partial W_2=a_1^\top dz_2$、$\partial b_2=\sum dz_2$（矩阵乘对输入的梯度是「对方梯度 × 本层输入的转置」）；2）$da_1=dz_2W_2^\top$；3）ReLU 反向是 mask：$dz_1=da_1\odot\mathbb{1}[z_1>0]$（或等价地 $a_1>0$）；4）$\partial W_1=X^\top dz_1$、$\partial b_1=\sum dz_1$。

**易错点**：1）形状转置方向（$X^\top dz$ 还是 $dz^\top X$）靠「梯度形状必须等于参数形状」自查；2）ReLU 的 mask 用 `z1 > 0` 还是 `a1 > 0` 等价，但用 `a1` 时若初始化把 0 映射进来会有细微差异；3）softmax 与 CE 合并后 $\partial z_2$ 才是干净的 $(p-y)/N$，若分开推要处理 softmax 雅可比矩阵；4）He 初始化 $\mathcal{N}(0, 2/d_{in})$ 配 ReLU，防止逐层方差衰减。

**复杂度**：前向 $O(N(d_{in}h + hd_{out}))$，反向约 2 倍前向；这就是「backward ≈ 2×forward FLOPs，加上激活存储」的由来。

**追问**：为什么要存中间激活（反向要用 a1，训练显存大头）；梯度检查（gradcheck）的适用 eps 与误差量级（中心差分 $O(\epsilon^2)$）。''',
        "keyPoints": [
            "softmax+CE 合并的反向起点：dz2 = (p − onehot)/N",
            "dW = 输入转置 @ 上游梯度，形状自查：梯度形状 == 参数形状",
            "ReLU 反向 = 上游梯度 × (z1 > 0) 的 0/1 mask",
            "He 初始化 N(0, 2/d_in) 配 ReLU 保持方差",
            "反向 FLOPs 约为前向 2 倍，需缓存中间激活",
        ],
        "followUps": [
            {"q": "为什么反向比前向慢？", "a": "反向要为每个参数算梯度：dW 需要 X^T·dz（与该层前向同量级的矩阵乘），还要回传 dz 给上一层，计算量约为前向的 2 倍；再加上激活读写，实测一个 step 反向通常占 60%~70% 时间。"},
        ],
        "code": {
            "lang": "python",
            "caption": "numpy 两层 MLP 前向 + 反向 + 数值梯度抽查",
            "content": r'''import numpy as np

def init_params(d_in, h, d_out, seed=0):
    rng = np.random.default_rng(seed)
    return {
        'W1': rng.normal(0, np.sqrt(2 / d_in), (d_in, h)),   # He 初始化配 ReLU
        'b1': np.zeros(h),
        'W2': rng.normal(0, np.sqrt(2 / h), (h, d_out)),
        'b2': np.zeros(d_out),
    }

def forward(p, X):
    z1 = X @ p['W1'] + p['b1']
    a1 = np.maximum(z1, 0)                              # ReLU
    z2 = a1 @ p['W2'] + p['b2']
    z2 = z2 - z2.max(-1, keepdims=True)                 # softmax 数值稳定
    e = np.exp(z2)
    probs = e / e.sum(-1, keepdims=True)
    return probs, {'X': X, 'a1': a1, 'probs': probs}

def backward(p, cache, y):
    X, a1, probs = cache['X'], cache['a1'], cache['probs']
    n = X.shape[0]
    dz2 = probs.copy()
    dz2[np.arange(n), y] -= 1.0
    dz2 /= n                                            # dL/dz2 = (p - onehot)/N
    dz1 = (dz2 @ p['W2'].T) * (a1 > 0)                  # ReLU 反向 mask
    return {
        'W2': a1.T @ dz2, 'b2': dz2.sum(0),
        'W1': X.T @ dz1, 'b1': dz1.sum(0),
    }

if __name__ == '__main__':
    rng = np.random.default_rng(0)
    X = rng.normal(size=(32, 4))
    y = rng.integers(0, 3, 32)
    p = init_params(4, 8, 3)
    probs, cache = forward(p, X)
    assert probs.shape == (32, 3) and abs(probs.sum(1).mean() - 1) < 1e-6
    grads = backward(p, cache, y)
    assert grads['W1'].shape == p['W1'].shape and grads['b2'].shape == p['b2'].shape
    def loss(pp):                                       # 供数值梯度使用
        pr, _ = forward(pp, X)
        return -np.log(pr[np.arange(32), y] + 1e-12).mean()
    eps = 1e-5
    for key, idx in [('W1', (0, 0)), ('W2', (1, 2)), ('b1', (3,))]:
        pp = {k: v.copy() for k, v in p.items()}
        pp[key][idx] += eps; l1 = loss(pp)
        pp[key][idx] -= 2 * eps; l0 = loss(pp)
        num = (l1 - l0) / (2 * eps)
        assert abs(num - grads[key][idx]) < 1e-6, (key, num, grads[key][idx])
    print('numpy mlp fwd+bwd ok')''',
        },
    },

    {
        "id": "handcoded-024",
        "topic": "训练组件",
        "type": "手撕",
        "difficulty": 2,
        "frequency": 3,
        "companies": ["字节", "智谱"],
        "years": ["2024", "2025"],
        "question": "手写 warmup + cosine 退火学习率调度器，验证关键节点的学习率取值与单调性。",
        "answerMd": r'''**思路一句话**：前 warmup 步线性从 0 升到 base_lr，之后按 $\eta_t = \eta_{min} + \frac{\eta_{max}-\eta_{min}}{2}\left(1+\cos\frac{\pi (t-w)}{T-w}\right)$ 余弦退火到 min_ratio×base。

**实现要点**：1）step 计数从 1 开始（第 1 步学习率 = base/warmup 而不是 0）；2）progress 超过 1 时要 clamp（训练步数超预算时不让 cos 走第二周期）；3）边界取值自查：warmup 末 = base_lr、终点 = min_ratio × base_lr。

**为什么这两段配合**：warmup 解决初期 Adam 二阶矩冷启动 + 大学习率踢飞参数的问题（占总步数 0.5%~2%）；cosine 让后期平滑收小步长精细收敛，且只有一个超参（总步数），比 step decay 少调参。GPT-3/LLaMA 均为此调度。

**易错点**：1）总步数与实际训练步数不一致时，cosine 中段断点重启（train 不到位、ckpt 续训）会让学习率跳变，工程上用 WSD（warmup-stable-decay）调度规避；2）warmup 从 0 起步还是从 0.1×base 起步，各框架不同要说清；3）min_lr_ratio=0 时末端为 0，续训会学不动，常见取 0.1。

**复杂度**：每步 $O(1)$。''',
        "keyPoints": [
            "线性 warmup 到 base_lr，再 cosine 退火到 min_ratio×base",
            "step 从 1 计，progress 要 clamp 到 1",
            "warmup 约 0.5%~2% 总步数，防 Adam 冷启动发散",
            "续训断点会导致中段 cos 跳变，可用 WSD 规避",
            "每步 O(1)，超参只有总步数",
        ],
        "followUps": [
            {"q": "WSD 调度和 cosine 有什么区别？各适合什么场景？", "a": "WSD（warmup-stable-decay）：长期保持 base_lr，只在最后 10%~20% 快速衰减。优点是随时可以停在任意稳定点拿一个可用的 checkpoint（数据扩展实验友好、continuous scaling），MiniMax/MiniCPM 系列采用；cosine 则必须按预算训满。"},
        ],
        "code": {
            "lang": "python",
            "caption": "warmup + cosine 调度器与边界值自检",
            "content": r'''import math

class WarmupCosine:
    def __init__(self, total_steps, warmup_steps, base_lr=1e-3, min_lr_ratio=0.1):
        assert 0 < warmup_steps < total_steps
        self.total, self.warm = total_steps, warmup_steps
        self.base, self.min_ratio = base_lr, min_lr_ratio
        self.step_num = 0

    def step(self):
        self.step_num += 1
        t = self.step_num
        if t <= self.warm:                       # 线性 warmup: 0 -> base
            lr = self.base * t / self.warm
        else:                                    # cosine 退火到 min_ratio * base
            progress = min((t - self.warm) / (self.total - self.warm), 1.0)
            lr = self.base * (self.min_ratio + (1 - self.min_ratio) *
                              0.5 * (1 + math.cos(math.pi * progress)))
        return lr

if __name__ == '__main__':
    sch = WarmupCosine(total_steps=1000, warmup_steps=100, base_lr=1e-3)
    lrs = [sch.step() for _ in range(1000)]
    assert abs(lrs[0] - 1e-5) < 1e-9             # 第 1 步 = base / 100
    assert abs(lrs[99] - 1e-3) < 1e-9            # warmup 末端达峰值
    assert abs(lrs[999] - 1e-4) < 1e-9           # 终点 = min_ratio * base
    assert all(a <= b + 1e-12 for a, b in zip(lrs[:100], lrs[1:100]))   # 上升段单调
    assert all(a >= b - 1e-12 for a, b in zip(lrs[100:], lrs[101:]))    # 下降段单调
    over = WarmupCosine(total_steps=10, warmup_steps=2).step  # 超预算不越界
    for _ in range(20):
        lr = over()
        assert 1e-4 - 1e-12 <= lr <= 1e-3 + 1e-12
    print('warmup+cosine ok')''',
        },
    },

    {
        "id": "handcoded-025",
        "topic": "训练组件",
        "type": "手撕",
        "difficulty": 4,
        "frequency": 3,
        "companies": ["华为", "腾讯", "Momenta"],
        "years": ["2024", "2025"],
        "question": "用 numpy 手写 BatchNorm 的训练/推理双模式前向与训练模式反向，数值梯度对拍。",
        "answerMd": r'''**思路一句话**：训练时沿 batch 维算 $\mu,\sigma^2$ 归一化（$y=\gamma\hat x+\beta$，$\hat x=(x-\mu)/\sqrt{\sigma^2+\epsilon}$），并用滑动平均维护 running stats 供推理直接使用；反向要对「统计量依赖 x」做完整推导。

**前向双模式**：训练用当前 batch 统计量（有偏方差，除 N）；推理用 running_mean/var（不动当前 batch），这是 BN 训推不一致的根源，也是小 batch/分布式下 SyncBN 存在的原因。

**反向公式**（紧凑形式，设 $g=\partial L/\partial y\cdot\gamma$，沿 batch 维 N）：

$$\frac{\partial x}{\partial L}=\frac{1}{N}\cdot\frac{1}{\sqrt{\sigma^2+\epsilon}}\left(N g-\sum g-\hat x\sum(g\hat x)\right)$$

与 LayerNorm 的反向同构（只是统计维度换到 batch），三项分别对应主梯度、均值路径、方差路径。$\partial\gamma=\sum g\hat x$、$\partial\beta=\sum g$。

**易错点**：1）归一化用有偏方差，但 PyTorch 的 running_var 更新用的是无偏估计（$\frac{N}{N-1}\sigma^2$），对拍显存行为时要留意；2）momentum 语义是「新值权重」：`running = (1-m)*running + m*batch`；3）推理分支没有反向（grad 不流经 running stats）。

**复杂度**：前向 $O(ND)$；反向同阶。CNN 中沿 (N,H,W) 归一化，本简化版沿 N。

**追问**：为什么大模型都用 LN 不用 BN（序列变长、推理无 batch、对 batch 内相关性敏感）；GroupNorm 折中了什么。''',
        "keyPoints": [
            "训练用 batch 统计量，推理用 running mean/var（滑动平均）",
            "归一化用有偏方差；PyTorch running_var 用无偏估计，注意对拍口径",
            "反向三项式：主项 − 均值路径 − 方差路径，1/N · 1/σ 系数",
            "running 更新语义：new = (1−m)·old + m·batch",
            "统计量沿 batch 维，训练/推理行为不一致是 BN 的固有痛点",
        ],
        "followUps": [
            {"q": "batch=1 时 BN 会怎样？", "a": "方差为 0，归一化退化为恒等（除以 sqrt(0+eps)），且 running stats 若未充分预热会严重失真。所以 BN 不适合小 batch/序列任务；分布式下用 SyncBN 跨卡聚合统计量，或改用 GN/LN。"},
        ],
        "code": {
            "lang": "python",
            "caption": "BatchNorm 训练/推理前向 + 训练模式反向 + 数值对拍",
            "content": r'''import numpy as np

def bn_forward(x, gamma, beta, running_mean, running_var,
               eps=1e-5, momentum=0.1, training=True):
    if training:
        mu = x.mean(0)                          # 沿 batch 维统计
        var = x.var(0)                          # 有偏方差
        xhat = (x - mu) / np.sqrt(var + eps)
        running_mean = (1 - momentum) * running_mean + momentum * mu
        running_var = (1 - momentum) * running_var + momentum * var
        cache = (xhat, gamma, var, eps)
    else:
        xhat = (x - running_mean) / np.sqrt(running_var + eps)
        cache = None                            # 推理路径无反向
    return gamma * xhat + beta, cache, running_mean, running_var

def bn_backward(dout, cache):
    xhat, gamma, var, eps = cache
    n = dout.shape[0]
    g = dout * gamma
    inv_std = 1.0 / np.sqrt(var + eps)
    # 与 LayerNorm 同构的三项式反向（统计维换到 batch）
    dx = inv_std / n * (n * g - g.sum(0) - xhat * (g * xhat).sum(0))
    return dx, (dout * xhat).sum(0), dout.sum(0)      # dx, dgamma, dbeta

if __name__ == '__main__':
    rng = np.random.default_rng(0)
    x = rng.normal(size=(8, 3))
    gamma, beta = rng.normal(size=3), rng.normal(size=3)
    rm, rv = np.zeros(3), np.ones(3)
    out, cache, rm2, rv2 = bn_forward(x, gamma, beta, rm, rv)
    assert out.shape == x.shape
    assert np.allclose(out.mean(0), beta, atol=1e-8)   # 归一化后 batch 均值 = beta
    assert np.all(rv2 > 0)                       # running var 已更新
    dout = rng.normal(size=(8, 3))
    dx, dgamma, dbeta = bn_backward(dout, cache)
    eps_num = 1e-6
    def bumped(delta, arr, name):
        a = arr.copy(); a[idx] += delta          # idx 由循环赋值
        if name == 'dx':
            return (bn_forward(a, gamma, beta, rm, rv)[0] * dout).sum()
        if name == 'dgamma':
            return (bn_forward(x, a, beta, rm, rv)[0] * dout).sum()
        return (bn_forward(x, gamma, a, rm, rv)[0] * dout).sum()
    for arr, ana, name, idx in [(x, dx, 'dx', (0, 1)),
                                (gamma, dgamma, 'dgamma', (2,)),
                                (beta, dbeta, 'dbeta', (1,))]:
        num = (bumped(eps_num, arr, name) - bumped(-eps_num, arr, name)) / (2 * eps_num)
        assert abs(num - ana[idx]) < 1e-5, (name, num, ana[idx])
    o_inf, c_inf, _, _ = bn_forward(x, gamma, beta, rm2, rv2, training=False)
    assert c_inf is None and o_inf.shape == x.shape   # 推理模式走 running stats
    print('batchnorm fwd+bwd ok')''',
        },
    },

    # ---------------------------------------------------------------- 高频算法题
    {
        "id": "handcoded-026",
        "topic": "高频算法题",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 5,
        "companies": ["字节", "快手", "拼多多", "腾讯"],
        "years": ["2024", "2025"],
        "question": "手写 LRU Cache，get/put 均 O(1)，并跑通淘汰顺序断言。",
        "answerMd": r'''**思路一句话**：哈希表 + 双向链表：哈希 O(1) 定位节点，双向链表 O(1) 摘除/头插维护访问顺序，容量满淘汰链表尾部（最久未用）。Python 里 `OrderedDict` 一把梭，面试常要求再手写链表版。

**OrderedDict 版**：`get` 命中要 `move_to_end(key)`（提到最新端）；`put` 已存在则更新并提前，不存在则插入；超容 `popitem(last=False)` 弹最旧。手写版则是 dummy head/tail 哨兵 + `_remove(node)` + `_add_front(node)` 三个原语，注意 put 已有 key 时「先摘下再头插」。

**易错点**：1）get 命中也要更新顺序（LRU 的 U 是 used，不只是 put）；2）put 已存在的 key 要更新值且视为一次访问；3）容量为 0/1 的边界；4）淘汰时「先判断容量再插入」还是「先插入再淘汰」要保持一致。

**复杂度**：get/put 均 $O(1)$ 时间，$O(capacity)$ 空间。

**工程迁移（加分项）**：推理引擎的 KV cache 块管理（vLLM 前身 Orca 的 paged 管理、前缀 cache 淘汰）、Redis 的近似 LRU（采样淘汰）、操作系统页面置换都是同一思想。''',
        "keyPoints": [
            "哈希定位 + 双向链表维护访问顺序，双 O(1)",
            "get 命中也要 move_to_end，U 是 used",
            "put 已有 key：更新值且视为访问；满容淘汰尾部最旧",
            "OrderedDict 是标准解，手写版用 dummy 哨兵防边界",
            "同思想迁移：KV cache 块淘汰、Redis LRU、页面置换",
        ],
        "followUps": [
            {"q": "LFU 和 LRU 的区别？LFU 怎么做到 O(1)？", "a": "LRU 淘汰最久未访问，LFU 淘汰访问频次最低。O(1) LFU 用「频次桶 + 桶内双向链表」两个维度的链表：freq->list，节点在访问时跨桶移动，min_freq 只增不减平摊 O(1)。"},
            {"q": "线程安全的 LRU 要加什么？", "a": "最简单是全局锁（读写都串行）；高并发用分片（shard by key hash，类似 ConcurrentHashMap 思路）降低锁竞争，或读操作用无锁快照 + 写后失效。"},
        ],
        "code": {
            "lang": "python",
            "caption": "LRU Cache（OrderedDict 版，get/put O(1)）",
            "content": r'''from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity):
        self.cap = capacity
        self.od = OrderedDict()

    def get(self, key):
        if key not in self.od:
            return -1
        self.od.move_to_end(key)             # 命中即提为最新
        return self.od[key]

    def put(self, key, value):
        if key in self.od:
            self.od.move_to_end(key)
        self.od[key] = value
        if len(self.od) > self.cap:          # 淘汰头部（最久未用）
            self.od.popitem(last=False)

if __name__ == '__main__':
    c = LRUCache(2)
    c.put(1, 1); c.put(2, 2)
    assert c.get(1) == 1                     # 1 变最新
    c.put(3, 3)                              # 满，淘汰 2
    assert c.get(2) == -1
    c.put(4, 4)                              # 淘汰 1
    assert c.get(1) == -1 and c.get(3) == 3 and c.get(4) == 4
    c.put(3, 30)                             # 已存在：更新且提前
    assert c.get(3) == 30 and c.get(4) == 4
    c1 = LRUCache(1)                         # 容量 1 边界
    c1.put(9, 9); c1.put(8, 8)
    assert c1.get(9) == -1 and c1.get(8) == 8
    print('lru ok')''',
        },
    },

    {
        "id": "handcoded-027",
        "topic": "高频算法题",
        "type": "手撕",
        "difficulty": 2,
        "frequency": 5,
        "companies": ["字节", "阿里", "美团"],
        "years": ["2024", "2025"],
        "question": "手写 TopK：用大小为 k 的小根堆求最大的 k 个数，分析为什么不用大根堆。",
        "answerMd": r'''**思路一句话**：维护一个大小为 k 的小根堆，堆顶是「当前第 k 大」；新元素比堆顶大才有戏，`heapreplace` 弹顶压入。扫完堆里就是最大的 k 个。

**为什么是小根堆**：我们只需要和「第 k 大的门槛」比较——堆顶恰是门槛，$O(1)$ 读取、$O(\log k)$ 更新；大根堆顶是最大值，无法 O(1) 拿到门槛。

**实现要点**：1）`heapreplace(heap, x)` = pop + push 一次完成，比分开调用少一半 sift；2）k≥n 直接排序返回，k≤0 返回空；3）结果要 `sorted(reverse=True)` 输出（堆本身无序）；4）有重复值时返回的是「值的重数」意义下的 top-k，与全排序前 k 一致。

**复杂度**：$O(n\log k)$ 时间、$O(k)$ 空间——n≫k 时显著优于全排序 $O(n\log n)$；流式数据也适用（这正是「堆」版本的杀手锏）。备选方案：快速选择 $O(n)$ 期望但需全部数据在内存且不改流式；海量数据外存用多路归并。

**追问**：10 亿个数取 top-100、内存有限怎么办（分桶/计数或堆 + 外排）；beam search 本质就是带优先队列的 top-k。''',
        "keyPoints": [
            "小根堆维护 k 个候选，堆顶 = 当前第 k 大门槛",
            "heapreplace 一次完成弹出+压入，比 pop+push 快",
            "时间 O(n log k)、空间 O(k)，支持流式输入",
            "快选期望 O(n) 更快但不适流式、会打乱原数组",
            "与 beam search / 检索召回共用同一优先队列思想",
        ],
        "followUps": [
            {"q": "如果要求第 k 大而不是前 k 个呢？", "a": "同一个堆，扫完后堆顶即答案；或用快速选择（随机 pivot + 三路划分）期望 O(n)。面试常连着问：堆适合流式和取集合，快选适合一次性取单个次序统计量。"},
        ],
        "code": {
            "lang": "python",
            "caption": "小根堆 TopK 与全排序对拍",
            "content": r'''import heapq
import random

def top_k(nums, k):
    if k <= 0:
        return []
    heap = []                                # 小根堆：堆顶是第 k 大门槛
    for x in nums:
        if len(heap) < k:
            heapq.heappush(heap, x)
        elif x > heap[0]:
            heapq.heapreplace(heap, x)       # 弹顶压入一步完成
    return sorted(heap, reverse=True)

if __name__ == '__main__':
    assert top_k([3, 1, 4, 1, 5, 9, 2, 6], 3) == [9, 6, 5]
    assert top_k([1, 2], 0) == [] and top_k([], 3) == []
    assert top_k([7, 7, 7], 2) == [7, 7]     # 重复值按重数取
    random.seed(0)
    nums = [random.randint(0, 100) for _ in range(1000)]
    assert top_k(nums, 5) == sorted(nums, reverse=True)[:5]   # 与全排序对拍
    print('topk ok')''',
        },
    },

    {
        "id": "handcoded-028",
        "topic": "高频算法题",
        "type": "手撕",
        "difficulty": 2,
        "frequency": 5,
        "companies": ["字节", "快手", "小红书"],
        "years": ["2024", "2025"],
        "question": "手写「无重复字符的最长子串」（滑动窗口），重点讲 left 边界的收缩条件。",
        "answerMd": r'''**思路一句话**：双指针维护「无重复」窗口，哈希表记录每个字符最近出现位置；右指针扩张时若字符已在窗口内，left 直接跳到「上次出现位置 + 1」，全程每字符只进出一次。

**收缩条件的坑（本题核心）**：`left = last[ch] + 1` 之前必须判断 `last[ch] >= left`——上次出现位置可能在窗口左侧之外，此时不能把 left 往回退（左移），否则窗口失效。用 'abba' 这个用例就能测出来：处理末尾 a 时 last[a]=0 < left=2，left 不动。

**两种等价写法**：1）哈希存「最近下标」（本实现，left 跳跃）；2）哈希存「窗口内字符计数」，重复时 while 循环逐个右移 left 并减计数（慢一点但通用，可处理「至多 k 种字符」类变体）。

**易错点**：1）更新 `best` 的时机放在窗口更新之后每轮做；2）空串返回 0；3）变体「至多 k 个不同字符的最长子串」要用计数写法；4）字符集很大时（Unicode）用 dict 而不是定长数组。

**复杂度**：时间 $O(n)$（left 只前进不后退，摊还分析）；空间 $O(\min(\Sigma, n))$，$\Sigma$ 为字符集大小。

**追问**：返回子串本身怎么改（记录 best 起点）；「至多 K 种字符」模板怎么写；滑动窗口适用的充要条件（窗口指标随扩张单调）。''',
        "keyPoints": [
            "哈希存字符最近下标，left 直接跳到 last[ch]+1",
            "跳跃前必须判断 last[ch] >= left，防 left 回退（'abba' 用例）",
            "时间 O(n)：left/right 都单调前进",
            "计数版模板可解「至多 K 种字符」类变体",
            "空间 O(min(字符集, n))",
        ],
        "followUps": [
            {"q": "如果要求返回最长子串本身？", "a": "更新 best 时记录起点 start = left 和长度，最后 return s[start:start+best]。注意 best 更新时机在窗口调整完成之后，起点才是合法窗口的左端。"},
        ],
        "code": {
            "lang": "python",
            "caption": "滑动窗口求无重复字符最长子串",
            "content": r'''def length_of_longest_substring(s):
    last = {}                     # 字符 -> 最近出现下标
    left = 0
    best = 0
    for i, ch in enumerate(s):
        if ch in last and last[ch] >= left:   # 上次出现在窗口内才需要收缩
            left = last[ch] + 1               # 直接跳跃，left 永不回退
        last[ch] = i
        best = max(best, i - left + 1)
    return best

if __name__ == '__main__':
    assert length_of_longest_substring('abcabcbb') == 3    # abc
    assert length_of_longest_substring('bbbbb') == 1
    assert length_of_longest_substring('pwwkew') == 3      # wke
    assert length_of_longest_substring('') == 0
    assert length_of_longest_substring('abba') == 2        # 经典回退陷阱用例
    assert length_of_longest_substring('dvdf') == 3        # vdf
    print('longest substring ok')''',
        },
    },

    {
        "id": "handcoded-029",
        "topic": "高频算法题",
        "type": "手撕",
        "difficulty": 2,
        "frequency": 3,
        "companies": ["美团", "拼多多"],
        "years": ["2024", "2025"],
        "question": "手写合并区间：按左端点排序后一趟扫描，处理相接与包含两类边界。",
        "answerMd": r'''**思路一句话**：按左端点排序后，当前区间与结果最后一个区间「左端点 ≤ 上一右端点」就合并（右端点取 max），否则新开一段。排序保证只需与最后一个比较。

**为什么右端点要取 max**：排序按左端点，但右端点不单调，`[1,10]` 后跟 `[2,3]` 是包含关系，若直接赋值 `out[-1][1] = r` 会把 10 丢掉——必须 `max(out[-1][1], r)`，这是本题最高频的 bug。

**边界约定**：1）`l == out[-1][1]` 相接（如 [1,4] 和 [4,5]）要不要合并，取决于区间是闭区间还是左闭右开，LeetCode 语义是闭区间要合并，说清楚即可；2）空输入返回空表；3）原地修改 vs 返回新列表。

**复杂度**：排序 $O(n\log n)$ 主导，扫描 $O(n)$；空间 $O(n)$（输出）。若输入已按左端点有序，可降为 $O(n)$。

**变体追问**：插入区间（先二分定位再合并）；无重叠区间问题（按右端点贪心，即区间调度）；判断区间集合是否能完全覆盖目标区间。''',
        "keyPoints": [
            "按左端点排序，一趟扫描只与结果最后一个区间比较",
            "合并时右端点取 max，防止包含关系丢右边界",
            "相接（l == 上一右端点）是否合并要和面试官确认语义",
            "时间 O(n log n)，已排序时 O(n)",
            "变体：插入区间 / 区间调度贪心按右端点",
        ],
        "followUps": [
            {"q": "如果区间是海量且无法全部载入内存？", "a": "外部排序按左端点流式归并，维护一个当前合并中的区间，逐块读取；本质还是排序 + 单趟扫描，只是排序换成了外排 k 路归并。"},
        ],
        "code": {
            "lang": "python",
            "caption": "合并区间（排序 + 一趟扫描）",
            "content": r'''def merge_intervals(intervals):
    if not intervals:
        return []
    intervals = sorted(intervals)                # 按左端点排序 O(n log n)
    out = [list(intervals[0])]
    for l, r in intervals[1:]:
        if l <= out[-1][1]:                      # 相交或相接
            out[-1][1] = max(out[-1][1], r)      # 右端点取 max，防包含关系丢值
        else:
            out.append([l, r])
    return out

if __name__ == '__main__':
    assert merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
    assert merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]            # 相接合并
    assert merge_intervals([[1, 10], [2, 3], [4, 5]]) == [[1, 10]]  # 包含关系
    assert merge_intervals([[5, 6], [1, 2]]) == [[1, 2], [5, 6]]    # 输入无序
    assert merge_intervals([]) == []
    print('merge intervals ok')''',
        },
    },

    {
        "id": "handcoded-030",
        "topic": "高频算法题",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 4,
        "companies": ["字节", "华为", "蔚来"],
        "years": ["2024", "2025"],
        "question": "手写旋转有序数组的二分查找（LeetCode 33 变体），讲清「每次必有一半有序」的判据。",
        "answerMd": r'''**思路一句话**：旋转数组把有序段劈成两半，`nums[l] <= nums[m]` 说明左半 `[l,m]` 是有序的，否则右半 `[m,r]` 有序；在有序的一半里做常规范围判断，另一半递归进无序段——每次丢掉一半，保持 $O(\log n)$。

**判断逻辑**：1）`nums[m] == target` 直接返回；2）左半有序时：`nums[l] <= target < nums[m]` 则 target 在左半（`r = m-1`），否则去右半；3）右半有序时对称：`nums[m] < target <= nums[r]` 则 `l = m+1`，否则去左半。

**易错点**：1）`nums[l] <= nums[m]` 的等号——l==m 时（一两个元素）左半只有一个元素也算有序，漏掉等号会在 [3,1] 这类用例出错；2）边界用闭区间 `[l,r]` 时循环条件 `l <= r`、更新是 `m±1`，别和左闭右开混用；3）进阶变体：找最小值（LeetCode 153，比较对象换成 `nums[m]` 与 `nums[r]`）、有重复元素的最坏 $O(n)$（等于时 `r-=1` 防御）。

**复杂度**：$O(\log n)$ 时间、$O(1)$ 空间；重复元素最坏退化 $O(n)$。

**追问**：找旋转点（最小值）的二分怎么写（`nums[m] > nums[r]` 时最小值在右侧）；为什么比较 `nums[r]` 而不是 `nums[l]`（防未旋转时误判）。''',
        "keyPoints": [
            "nums[l] <= nums[m] 则左半有序，否则右半有序，等号不可漏",
            "在有序半段做范围判断决定去留，保持 O(log n)",
            "闭区间模板：l<=r 循环、m±1 更新",
            "重复元素最坏退化为 O(n)，等于时需防御性收缩",
            "找最小值变体：比较 nums[m] 与 nums[r]",
        ],
        "followUps": [
            {"q": "怎么找旋转数组的最小值？", "a": "while l<r: m=(l+r)//2，若 nums[m]>nums[r] 最小值在 (m,r]，l=m+1；否则在 [l,m]，r=m。结束时 nums[l] 即最小值。关键是比较 nums[r]：与 nums[l] 比较在未旋转（本身就是有序）时会误判。"},
        ],
        "code": {
            "lang": "python",
            "caption": "旋转有序数组二分查找",
            "content": r'''def search_rotated(nums, target):
    l, r = 0, len(nums) - 1
    while l <= r:
        m = (l + r) // 2
        if nums[m] == target:
            return m
        if nums[l] <= nums[m]:                   # 左半 [l, m] 有序（等号处理 l==m）
            if nums[l] <= target < nums[m]:
                r = m - 1
            else:
                l = m + 1
        else:                                    # 右半 [m, r] 有序
            if nums[m] < target <= nums[r]:
                l = m + 1
            else:
                r = m - 1
    return -1

def find_min(nums):
    l, r = 0, len(nums) - 1                      # 变体：找旋转点最小值
    while l < r:
        m = (l + r) // 2
        if nums[m] > nums[r]:
            l = m + 1
        else:
            r = m
    return nums[l]

if __name__ == '__main__':
    assert search_rotated([4, 5, 6, 7, 0, 1, 2], 0) == 4
    assert search_rotated([4, 5, 6, 7, 0, 1, 2], 3) == -1
    assert search_rotated([1], 1) == 0
    assert search_rotated([3, 1], 1) == 1        # 等号遗漏会挂的用例
    assert search_rotated([5, 1, 3], 5) == 0
    assert find_min([4, 5, 6, 7, 0, 1, 2]) == 0
    assert find_min([1, 2, 3]) == 1
    print('rotated binary search ok')''',
        },
    },

    {
        "id": "handcoded-031",
        "topic": "高频算法题",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 5,
        "companies": ["阿里", "百度", "腾讯"],
        "years": ["2024", "2025"],
        "question": "手写编辑距离（Levenshtein）DP，并说如何用滚动数组把空间降到 O(min(m,n))。",
        "answerMd": r'''**思路一句话**：$dp[i][j]$ = a 前 i 个字符变成 b 前 j 个字符的最少操作数；转移 $dp[i][j]=\min(dp[i-1][j-1]+\text{cost},\ dp[i-1][j]+1,\ dp[i][j-1]+1)$，相同字符 cost=0，否则 1（替换/删除/插入）。

**初始化与方向**：$dp[i][0]=i$（全删）、$dp[0][j]=j$（全插入）——第一行/列是空串的边界。逐行从上到下、从左到右填表。

**空间优化**：每个 $dp[i][j]$ 只依赖上一行同列/左列和本行左列，可用一行滚动 + 一个临时变量保存左上角（`prev_diag`），空间 $O(\min(m,n))$；若还要回溯编辑路径则必须保留全表 $O(mn)$。

**易错点**：1）下标偏移：字符串是 0-based，dp 是 1-based，比较 `a[i-1] == b[j-1]`；2）相同字符时必须直接继承对角线（不能还在三者里取 min 加 1）；3）hirschberg 分治可以做到 $O(\min(m,n))$ 空间还保留路径，面试提一句很加分。

**复杂度**：时间 $O(mn)$，空间 $O(mn)$ 或滚动 $O(\min(m,n))$。

**工程关联**：WER/CER（语音识别评测）、拼写纠错、DNA 序列比对（ Needleman-Wunsch 是它的加权版）本质都是这个 DP。''',
        "keyPoints": [
            "dp[i][j] 三来源：替换(对角)、删除(上)、插入(左)，相同字符零代价",
            "边界 dp[i][0]=i、dp[0][j]=j",
            "下标偏移：比较 a[i-1] 与 b[j-1]",
            "滚动数组 + prev_diag 变量降到 O(min(m,n))；回溯路径需全表",
            "工程迁移：WER/CER 评测、拼写纠错、序列比对",
        ],
        "followUps": [
            {"q": "怎么把空间优化到 O(min(m,n))？", "a": "让内层循环走较短的那个串；只保留一行 dp 与一个对角线暂存变量 prev_diag：新 dp[j] = min(prev_diag + cost, 上一行 dp[j] + 1, 本行 dp[j-1] + 1)，扫描前 prev_diag 初始化为上一行 dp[j-1]。"},
        ],
        "code": {
            "lang": "python",
            "caption": "编辑距离 DP（含滚动数组版）",
            "content": r'''def edit_distance(a, b):
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i                      # 全删除
    for j in range(n + 1):
        dp[0][j] = j                      # 全插入
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]           # 相同字符零代价
            else:
                dp[i][j] = 1 + min(dp[i - 1][j - 1],  # 替换
                                   dp[i - 1][j],      # 删除
                                   dp[i][j - 1])      # 插入
    return dp[m][n]

def edit_distance_1d(a, b):
    # 滚动数组版：空间 O(min(m,n))
    if len(a) < len(b):
        a, b = b, a                       # 让 b 是较短串
    prev = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [i] + [0] * len(b)
        diag = prev[0]                    # 左上角 dp[i-1][j-1]
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(diag + cost, prev[j] + 1, cur[j - 1] + 1)
            diag = prev[j]
        prev = cur
    return prev[-1]

if __name__ == '__main__':
    assert edit_distance('kitten', 'sitting') == 3
    assert edit_distance('intention', 'execution') == 5
    assert edit_distance('', 'abc') == 3
    assert edit_distance('same', 'same') == 0
    for x, y in [('kitten', 'sitting'), ('ab', 'ba'), ('', 'xyz')]:
        assert edit_distance(x, y) == edit_distance_1d(x, y)   # 两版互拍
    print('edit distance ok')''',
        },
    },

    {
        "id": "handcoded-032",
        "topic": "高频算法题",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 2,
        "companies": ["字节", "百度"],
        "years": ["2024"],
        "question": "手写最长公共子序列 LCS：DP 求长度并回溯构造一个具体的 LCS 字符串。",
        "answerMd": r'''**思路一句话**：$dp[i][j]$ = a 前 i 个与 b 前 j 个字符的 LCS 长度；字符相等时 $dp[i-1][j-1]+1$，否则 $\max(dp[i-1][j], dp[i][j-1])$；从 $(m,n)$ 回溯即可构造出一个 LCS。

**回溯规则**：相等字符 → 收下并走对角线；否则朝「较大的相邻 dp 值」方向走（`dp[i-1][j] >= dp[i][j-1]` 走上，否则走左）——只要始终朝不减小 dp 值的方向走，收集到的必然是合法 LCS。

**与编辑距离的关系（加分项）**：LCS 是编辑距离的特例——只允许插入和删除（cost=1）、替换 cost=2 时，$ed = m + n - 2\cdot|LCS|$；LCS 长度还可以刻画 diff 工具（我的 Myers diff 就是 LCS 变体）。

**易错点**：1）子序列 vs 子串：子串要求连续（对应 DP 是「相等时继承对角线、不等归零」），别混；2）回溯时构造的串是逆序的，要 reverse；3）多个最优解时本实现返回其中一个，面试说清即可。

**复杂度**：时间 $O(mn)$、空间 $O(mn)$（仅需长度可用滚动数组 $O(\min(m,n))$；构造具体序列可 Hirschberg 分治到线性空间）。

**追问**：最长公共子串怎么改（不等时归零、答案取全表 max）；LCS 的 $O(mn)$ 能不能再快（比特并行 bit-parallel 可到 $O(mn/w)$）。''',
        "keyPoints": [
            "相等：dp[i-1][j-1]+1；否则 max(上, 左)",
            "回溯朝不减小 dp 值的方向走，收集必为合法 LCS",
            "结果串回溯出来是逆序，需 reversed",
            "LCS 与编辑距离：cost=2 替换的 ed = m+n−2|LCS|",
            "最长公共子串是另一个 DP：不等归零取全表 max",
        ],
        "followUps": [
            {"q": "LCS 和最长重复子数组（连续）的区别？", "a": "连续版本（子数组/子串）转移不等时 dp 归 0，答案取整个 dp 表的最大值而不是 dp[m][n]；不连续版本（子序列）不等时取 max(上,左)。两者转移方程一字之差，面试常故意追问。"},
        ],
        "code": {
            "lang": "python",
            "caption": "LCS 长度 + 回溯构造具体序列",
            "content": r'''def lcs(a, b):
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    out = []                                   # 回溯构造一个 LCS
    i, j = m, n
    while i > 0 and j > 0:
        if a[i - 1] == b[j - 1]:
            out.append(a[i - 1])
            i -= 1; j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    return dp[m][n], ''.join(reversed(out))

if __name__ == '__main__':
    ln, s = lcs('ABCBDAB', 'BDCABA')
    assert ln == 4 and s in ('BCBA', 'BCAB', 'BDAB'), (ln, s)
    def is_subseq(sub, src):                   # 自检：确为两串公共子序列
        it = iter(src)
        return all(ch in it for ch in sub)
    assert is_subseq(s, 'ABCBDAB') and is_subseq(s, 'BDCABA')
    assert lcs('abc', 'abc') == (3, 'abc')
    assert lcs('', 'x') == (0, '')
    print('lcs ok:', ln, s)''',
        },
    },

    {
        "id": "handcoded-033",
        "topic": "高频算法题",
        "type": "手撕",
        "difficulty": 1,
        "frequency": 3,
        "companies": ["拼多多", "美团"],
        "years": ["2024", "2025"],
        "question": "手写大数加法：两个以字符串表示的非负整数相加，不允许直接转 int。",
        "answerMd": r'''**思路一句话**：竖式加法——双指针从最低位开始，逐位相加加进位，`s % 10` 落位、`s // 10` 进位，最后反转；循环条件带上 `carry` 处理最高位溢出。

**实现要点**：1）循环条件 `i >= 0 or j >= 0 or carry`，carry 忘加会丢最高位（'999'+'1' 用例）；2）取位用 `ord(ch) - 48`（或 int(ch)），越界时补 0；3）结果从低位往高位 append，最后 `''.join(reversed(out))`；4）变体要会说：负数（先比绝对值大小再做减法）、小数点、减法（借位版竖式）。

**易错点**：1）用 Python 的 int(s) 是违反题意的（虽然语言特性允许，面试官要看竖式逻辑）；2）reverse 忘了；3）'0'+'0' 应输出 '0' 而不是 '00'（逐位落位法天然不会前导零，除非手动特判，本实现 s%10 落位天然正确）。

**复杂度**：$O(\max(m,n))$ 时间、$O(\max(m,n))$ 空间（输出本身）。

**追问**：两个超长二进制串相加（同一套逻辑 base=2）；大数乘法（竖式乘 $O(mn)$ 或 FFT $O(n\log n)$）；为什么金融系统用字符串/定点数而不是 float（精度与舍入）。''',
        "keyPoints": [
            "双指针从低位起，s%10 落位、s//10 进位，最后 reverse",
            "循环条件必须包含 carry，防最高位丢失",
            "越界位补 0：i>=0 才取 ord(ch)-48",
            "逐位落位天然无前导零问题",
            "变体：二进制加法同逻辑、减法要借位与符号判断",
        ],
        "followUps": [
            {"q": "如果是两个大数相乘呢？", "a": "竖式乘：逐位乘累加到结果数组 O(mn)；面试加分项是 Karatsuba O(n^1.585) 分治或 FFT/NTT O(n log n)。工程里 Python 直接 int、Java 用 BigInteger，底层正是这些算法。"},
        ],
        "code": {
            "lang": "python",
            "caption": "字符串竖式大数加法，与 Python 大整数对拍",
            "content": r'''def big_add(a, b):
    i, j = len(a) - 1, len(b) - 1
    carry = 0
    out = []
    while i >= 0 or j >= 0 or carry:
        da = ord(a[i]) - 48 if i >= 0 else 0    # '0' 的 ASCII 是 48
        db = ord(b[j]) - 48 if j >= 0 else 0
        s = da + db + carry
        out.append(chr(s % 10 + 48))            # 落位
        carry = s // 10                         # 进位
        i -= 1; j -= 1
    return ''.join(reversed(out))

if __name__ == '__main__':
    assert big_add('123', '9') == '132'
    assert big_add('999', '1') == '1000'        # 连续进位
    assert big_add('0', '0') == '0'
    assert big_add('99999999999999999999', '2') == '100000000000000000001'
    import random
    random.seed(1)
    for _ in range(100):                        # 与 Python 原生大整数对拍
        x = random.randint(0, 10 ** 30)
        y = random.randint(0, 10 ** 30)
        assert big_add(str(x), str(y)) == str(x + y)
    print('big add ok')''',
        },
    },

    {
        "id": "handcoded-034",
        "topic": "高频算法题",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["字节", "快手"],
        "years": ["2024", "2025"],
        "question": "手写「数组中第 K 大的元素」快速选择（quickselect，随机 pivot），期望 O(n)。",
        "answerMd": r'''**思路一句话**：快排的分区思想但不递归两侧——partition 后 pivot 落位下标 p 与目标下标比较，只递归包含答案的那一侧，期望 $O(n)$（$n+n/2+n/4+\dots=2n$）。

**实现要点**：1）第 k 大 = 升序第 $n-k$ 位（0-based），先换算；2）随机选 pivot 防止有序输入退化成 $O(n^2)$（对抗构造数据）；3）分区用「挖坑法」：保存 pivot，从右找 <pivot 的填左坑、从左找 >pivot 的填右坑，最后坑位放回 pivot；4）递归改循环也行（尾递归消除）。

**易错点**：1）会修改原数组，需要时先拷贝（或用不可变写法但多 O(n) 空间）；2）「挖坑法」两个内层 while 的边界 `i < j` 与等号方向（`>=`/`<=`）配对错会死循环，尤其全相同元素时——写完用全相等数组自测；3）k 越界（k<1 或 k>n）要先挡。

**复杂度**：期望 $O(n)$、最坏 $O(n^2)$（随机化后概率极低）；空间 $O(\log n)$ 递归栈。对比：堆法 $O(n\log k)$ 适合流式。

**追问**：三路划分（Dutch flag）处理大量重复元素为什么更好（等于 pivot 的段直接排除）；BFPRT（median of medians）如何保证最坏 O(n)。''',
        "keyPoints": [
            "第 k 大 = 升序下标 n−k，只递归一侧，期望 O(n)",
            "随机 pivot 防退化；全相同元素用三路划分或验证不循环",
            "挖坑法分区：先从右扫再从左扫，坑位回填 pivot",
            "会修改原数组，必要时先拷贝",
            "堆版 O(n log k) 是流式场景的正解",
        ],
        "followUps": [
            {"q": "为什么三路划分对重复元素更友好？", "a": "两路划分遇大量重复时，等于 pivot 的元素被反复卷入分区，可能退化 O(n^2)；三路划分（<、=、> 三段）后等值段不再参与递归，重复越多越快，全相同数组 O(n) 收工。"},
        ],
        "code": {
            "lang": "python",
            "caption": "随机化快速选择求第 K 大",
            "content": r'''import random

def find_kth_largest(nums, k):
    assert 1 <= k <= len(nums)
    nums = list(nums)                            # 不污染调用方
    target = len(nums) - k                       # 升序第 target 位

    def quickselect(l, r):
        while True:
            if l == r:
                return nums[l]
            p = random.randint(l, r)             # 随机 pivot 防退化
            nums[l], nums[p] = nums[p], nums[l]
            pivot, i, j = nums[l], l, r
            while i < j:                         # 挖坑法分区
                while i < j and nums[j] >= pivot:
                    j -= 1
                nums[i] = nums[j]
                while i < j and nums[i] <= pivot:
                    i += 1
                nums[j] = nums[i]
            nums[i] = pivot
            if i == target:
                return nums[i]
            elif i < target:
                l = i + 1                        # 只递归目标一侧（循环实现）
            else:
                r = i - 1

    return quickselect(0, len(nums) - 1)

if __name__ == '__main__':
    assert find_kth_largest([3, 2, 1, 5, 6, 4], 2) == 5
    assert find_kth_largest([3, 2, 3, 1, 2, 4, 5, 5, 6], 4) == 4
    assert find_kth_largest([7, 7, 7, 7], 2) == 7            # 全重复
    assert find_kth_largest([1], 1) == 1
    random.seed(0)
    data = [random.randint(0, 100) for _ in range(500)]
    for k in (1, 7, 250, 500):
        assert find_kth_largest(data, k) == sorted(data)[len(data) - k]
    print('quickselect ok')''',
        },
    },

    # ---------------------------------------------------------------- 概率与采样
    {
        "id": "handcoded-035",
        "topic": "概率与采样",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 4,
        "companies": ["字节", "腾讯", "Google"],
        "years": ["2024", "2025"],
        "question": "只用 rand7() 实现 rand10()，要求期望均匀，并分析拒绝率与调用次数。",
        "answerMd": r'''**思路一句话**：两次 rand7() 拼出 49 个等概率状态（$(a-1)\times 7 + b \in [1,49]$），保留前 40 个映射到 1~10，落在 41~49 的重采样——拒绝采样框架。

**为什么是 40**：49 不是 10 的倍数，直接取模会有 9 个值多分到一次（概率 5/49 vs 4/49）不均匀；丢弃 9 个后 40 可被 10 整除，每个输出恰好 4 个来源状态，严格均匀。

**进阶（加分）**：被拒绝的 9 个状态别浪费——41~49 相当于拿到了一个均匀的 rand9，可以继续和下一次 rand7() 组合（49 状态 → 7×9=63，保留 60…），把期望调用次数从 $2\times\frac{49}{40}=2.45$ 降到约 2.21（理论下界 $\log_7 10\approx1.18$ 次信息论极限，工程取折中）。

**易错点**：1）`while True` 里每次都要重新采样两个数（不是只重采一个）；2）映射用 `(num-1) % 10 + 1` 保证 1~40 严格均匀分 10 组；3）面试可能追问「怎么证明均匀」——每个输出值恰好对应 4 个输入状态，条件概率相等；4）期望调用次数 ≠ 最坏（理论上可能长时间拒绝，概率指数衰减）。

**复杂度**：期望调用 rand7 约 2.21~2.45 次，$O(1)$ 空间。

**同型题**：rand5→rand7、用 rand2 构造 rand3、负采样里的拒绝修正。''',
        "keyPoints": [
            "(a−1)·7+b 构造 1..49 均匀状态，保留 40 个",
            "49 不能被 10 整除，直接取模不均匀，必须拒绝",
            "映射 (num−1)%10+1，每个输出恰 4 个来源状态",
            "期望调用约 2.45 次，可复用拒绝状态降到约 2.21",
            "框架即拒绝采样：接受域内映射、域外重采样",
        ],
        "followUps": [
            {"q": "怎么证明输出严格均匀？", "a": "输入空间 49 个等概率状态，接受域 40 个仍等概率（每个 1/49）；输出 v∈1..10 对应恰好 4 个接受状态，P(v)=4/49÷(40/49)=1/10。关键是接受域大小必须能被 10 整除。"},
        ],
        "code": {
            "lang": "python",
            "caption": "rand7 -> rand10 拒绝采样 + 均匀性统计验证",
            "content": r'''import random
from collections import Counter

def rand7():
    return random.randint(1, 7)

def rand10():
    while True:
        a, b = rand7(), rand7()
        num = (a - 1) * 7 + b              # 1..49，每个状态概率 1/49
        if num <= 40:                      # 拒绝 41..49
            return (num - 1) % 10 + 1      # 1..40 均匀分 10 组

if __name__ == '__main__':
    n = 70000
    cnt = Counter(rand10() for _ in range(n))
    assert len(cnt) == 10
    for v in range(1, 11):
        assert 6300 < cnt[v] < 7700, (v, cnt[v])   # 期望 7000，±10%
    # 拒绝率理论值 9/49 ≈ 0.184，期望每输出调用 2/(40/49) = 2.45 次 rand7
    print('rand7->rand10 ok, reject rate =', 9 / 49)''',
        },
    },

    {
        "id": "handcoded-036",
        "topic": "概率与采样",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 5,
        "companies": ["快手", "字节", "拼多多"],
        "years": ["2024", "2025"],
        "question": "手写蓄水池采样：数据流长度未知，等概率采 k 个，证明每个元素入选概率为 k/n。",
        "answerMd": r'''**思路一句话**：前 k 个直接进池；第 i（i>k）个以 $k/i$ 概率随机替换池中一个——归纳可证任意 n≥i 时池中恰是全量均匀 k 样本。

**证明（面试必讲）**：归纳法。n=k 时显然；假设 n=i−1 时每个元素在池概率 $k/(i-1)$，第 i 个以 $k/i$ 入池，池内旧元素被踢概率 $k/i\cdot 1/k=1/i$，留下概率 $(1-\frac1i)\cdot\frac{k}{i-1}=\frac{k}{i}$，新元素概率 $k/i$，均匀性保持。

**实现要点**：1）单遍、O(k) 空间、流式适用——这是它对比「先存全部再采样」的全部意义；2）`j = rng.randint(0, i)` 闭区间含 i；3）k 大于流长时全收（前 k 个逻辑覆盖）；4）分布式版本（各分片采 k 个、按分片大小加权合并）与 A-Res 加权版（按 $u^{1/w}$ 排序取 top-k）常被追问。

**易错点**：1）i 从 0 还是 1 计数、randint 闭区间开区间搞混会引入偏差；2）随机源要可重置（实验复现）；3）替换位置必须均匀选取，不能「总是替换第一个」。

**复杂度**：时间 $O(n)$ 单遍、空间 $O(k)$。

**应用**：海量日志采样、训练数据流式抽样、图采样（GraphSAGE 的邻居采样思想同源）。''',
        "keyPoints": [
            "前 k 个直进池，第 i 个以 k/i 概率替换随机一位",
            "归纳证明：旧元素留下概率恰为 k/i，均匀性保持",
            "单遍 O(n) 时间 O(k) 空间，适合长度未知的数据流",
            "randint 闭区间边界是常见偏差来源",
            "扩展：加权版 A-Res（u^(1/w) 排序）、分布式合并",
        ],
        "followUps": [
            {"q": "如果要按权重采样（重要元素更容易入选）怎么办？", "a": "A-Res 算法：给每个元素算 key = u^(1/w)（u 均匀随机），维护 key 最大的 k 个小顶堆，单遍流式完成加权蓄水池；或者用别名法+两阶段：先以概率选是否进入再替换。"},
        ],
        "code": {
            "lang": "python",
            "caption": "蓄水池采样 + 大规模均匀性验证",
            "content": r'''import random
from collections import Counter

def reservoir_sample(stream, k, seed=0):
    rng = random.Random(seed)
    res = []
    for i, item in enumerate(stream):
        if i < k:
            res.append(item)                 # 前 k 个直接进池
        else:
            j = rng.randint(0, i)            # [0, i] 均匀
            if j < k:
                res[j] = item                # 以 k/i 概率替换
    return res

if __name__ == '__main__':
    data = list(range(1000))
    cnt = Counter()
    runs = 2000
    for r in range(runs):
        s = reservoir_sample(data, 10, seed=r)
        assert len(s) == 10 and len(set(s)) == 10   # 无重复
        cnt.update(s)
    assert sum(cnt.values()) == runs * 10
    expect = runs * 10 / 1000                    # 每元素期望 20 次
    worst = min(cnt.values()), max(cnt.values())
    assert worst[0] > 2 and worst[1] < 45, worst  # 大体均匀（±3~5σ 界）
    print('reservoir ok, expect=%.1f, min/max = %s' % (expect, worst))''',
        },
    },

    {
        "id": "handcoded-037",
        "topic": "概率与采样",
        "type": "手撕",
        "difficulty": 2,
        "frequency": 3,
        "companies": ["美团", "腾讯"],
        "years": ["2024", "2025"],
        "question": "手写 Fisher-Yates 洗牌算法，证明 n! 种排列等概率，并说明错误写法为什么偏置。",
        "answerMd": r'''**思路一句话**：从后往前，位置 i 与「[0, i] 均匀随机」的 j 交换——第 i 位确定后不再动，剩余前缀继续；可证产生 n! 种排列各 $1/n!$ 概率。

**均匀性证明**：位置 n−1 有 n 种选择、n−2 有 n−1 种……总方案 $n\times(n-1)\times\dots\times1 = n!$，每个排列恰好对应唯一一条交换路径，且每步等概率——计数对齐即均匀。

**经典错误写法**（必讲）：1）从前往后、`j ∈ [0, n-1]`（不缩小范围）：产生 $n^n$ 条路径，无法被 n! 整除，必然偏置（n=3 时某些排列概率是其他 1.5 倍以上）；2）每次随机选两个位置交换 m 次：覆盖不均匀。面试让「找 bug」时这就是答案。

**易错点**：1）`rng.randint(0, i)` 是闭区间，含 i 自己（自己和自己交换合法，正是均匀性的一部分）；2）要在拷贝上洗（不污染原列表）或说明原地语义；3）Python 的 `random.shuffle` 就是 Fisher-Yates，自己写是为了讲清原理。

**复杂度**：$O(n)$ 时间、$O(1)$ 额外空间（原地）；范围缩小的区间用「swap-to-end」技巧可在数组上留下未洗前缀。

**应用**：负样本负采样前打乱、数据加载器 shuffle（DataLoader 的 RandomSampler）、A/B 分流。''',
        "keyPoints": [
            "从后往前，i 与 [0, i] 均匀随机 j 交换",
            "路径数恰好 n! 且每条等概率，故均匀",
            "错误写法：j 范围不缩小 → n^n 条路径除不尽 n!，产生偏置",
            "randint(0, i) 闭区间含自身，自交换合法且必要",
            "O(n) 时间原地完成",
        ],
        "followUps": [
            {"q": "怎么用实验验证洗牌均匀？", "a": "小 n（如 3）枚举所有排列计数：洗 M 次统计每种排列出现次数，做卡方检验看是否与均匀分布一致；代码里用 3000 次固定种子的计数 ±20% 界粗验。"},
        ],
        "code": {
            "lang": "python",
            "caption": "Fisher-Yates 洗牌 + 排列均匀性统计",
            "content": r'''import random
from collections import Counter

def shuffle(arr, seed=None):
    rng = random.Random(seed)
    a = list(arr)                        # 不污染原列表
    for i in range(len(a) - 1, 0, -1):   # 从后往前
        j = rng.randint(0, i)            # [0, i] 闭区间，含自身
        a[i], a[j] = a[j], a[i]
    return a

if __name__ == '__main__':
    assert sorted(shuffle([1, 2, 3, 4, 5])) == [1, 2, 3, 4, 5]
    assert shuffle([]) == [] and shuffle([7]) == [7]
    pos = Counter()
    for s in range(3000):                # 3! = 6 种排列应各约 500 次
        pos[tuple(shuffle([0, 1, 2], seed=s))] += 1
    assert len(pos) == 6
    for p, c in pos.items():
        assert abs(c - 500) < 100, (p, c)
    print('fisher-yates ok, counts:', dict(sorted(pos.items())))''',
        },
    },

    {
        "id": "handcoded-038",
        "topic": "概率与采样",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 2,
        "companies": ["字节", "Google"],
        "years": ["2024"],
        "question": "手写拒绝采样通用框架：从不可直接采样的分布 f(x) 采样（用均匀提议分布包络）。",
        "answerMd": r'''**思路一句话**：找一个易采样的提议分布 $g$ 和常数 $M$ 使 $f(x)\le M\cdot g(x)$ 处处成立；每次从 g 采 x、再以概率 $\frac{f(x)}{M g(x)}$ 接受，接受的样本精确服从 f。

**正确性直觉**：接受概率与 f 成正比，等于对 g 的分布做了「按 f 加权的筛选」；数学上 $P(\text{accept}\mid x)=f(x)/(Mg(x))$，贝叶斯反推 $P(x\mid \text{accept})\propto g(x)\cdot f(x)/(Mg(x))\propto f(x)$。

**实现要点**：1）M 的选取 = $\max_x f(x)/g(x)$，均匀提议时就是 $\max f \times \text{区间宽}$，再留一点余量防浮点越界；2）接受判据写成 `u * M * g(x) <= f(x)`（u~U(0,1)），别写成大于；3）返回「平均试验次数」可自检理论接受率 $\int f / M$。

**易错点**：1）M 不够大（包络没盖住 f）会采样出偏的分布——这是最难查的静默 bug；2）提议分布与 f 尾部形状差太远时接受率崩塌（高维尤其严重，维度灾难：接受率随维度指数下降），这也是高斯采样用 Box-Muller 而不是拒绝采样的原因；3）要提前算好 log 空间避免 underflow。

**复杂度**：每次接受期望 $M/\int f$ 次试验；一维下界 $O(1)$。

**关联**：rand7→rand10、负采样拒绝修正、粒子滤波的重要性采样都是近亲——重要性采样是「加权不拒绝」，拒绝采样是「拒绝不加权」。''',
        "keyPoints": [
            "包络条件 f(x) <= M·g(x) 必须处处成立，否则分布静默偏差",
            "接受概率 f(x)/(M·g(x))，接受样本精确服从 f",
            "期望接受率 = ∫f / M，M 越贴 f 越高效",
            "高维下接受率指数衰减，不适合直接上高维",
            "与重要性采样的区别：拒绝 vs 加权",
        ],
        "followUps": [
            {"q": "拒绝采样和重要性采样怎么选？", "a": "拒绝采样得到的是无偏精确样本，但需要包络且维数高时失效；重要性采样任何提议都能用（只要支撑集覆盖），但带来权重方差问题，权重塌缩时有效样本数骤降。低维精确采样用拒绝，高维积分估计用重要性/MCMC。"},
        ],
        "code": {
            "lang": "python",
            "caption": "拒绝采样框架：均匀提议采类正态分布",
            "content": r'''import random
import math

def rejection_sample(f_pdf, g_sample, g_pdf, M, n, seed=0):
    # 接受判据：u * M * g(x) <= f(x)；返回样本与平均试验次数
    rng = random.Random(seed)
    out, trials = [], 0
    while len(out) < n:
        x = g_sample(rng)
        u = rng.random()
        trials += 1
        if u * M * g_pdf(x) <= f_pdf(x):
            out.append(x)
    return out, trials / n

if __name__ == '__main__':
    target = lambda x: math.exp(-x * x / 2)          # f ∝ exp(-x^2/2)，[-4,4]
    g_sample = lambda rng: rng.uniform(-4, 4)        # 均匀提议
    g_pdf = lambda x: 1 / 8                          # 密度 1/区间宽
    M = 8.4                                          # max f/g = 8，留 5% 余量保证包络
    samples, acc = rejection_sample(target, g_sample, g_pdf, M, 20000)
    mean = sum(samples) / len(samples)
    var = sum((x - mean) ** 2 for x in samples) / len(samples)
    assert abs(mean) < 0.05, mean                    # 对称分布均值≈0
    assert 0.85 < var < 1.15, var                    # 方差≈1
    theo = math.sqrt(2 * math.pi) / M                # 理论接受率 ∫f / M
    assert abs(1.0 / acc - theo) < 0.02, (1.0 / acc, theo)   # acc 是平均试验次数
    print('rejection ok, accept=%.3f (theory %.3f)' % (1 / acc, theo))''',
        },
    },

    {
        "id": "handcoded-039",
        "topic": "概率与采样",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 2,
        "companies": ["DeepSeek", "智谱"],
        "years": ["2025"],
        "question": "手写 Gumbel-max trick：只用均匀随机数 + argmax 实现 categorical 采样，并说明它为何可导。",
        "answerMd": r'''**思路一句话**：给每个类别的 log 概率加一个 Gumbel(0,1) 噪声 $g_i=-\log(-\log u_i)$，取 argmax——结果精确服从 categorical(p)，把「按概率采样」变成了「加噪取最大」。

**为什么是 Gumbel**：Gumbel 是「极值型」分布——若 $X_i$ 独立加独立 Gumbel 噪声后取 max，则选中 i 的概率恰为 $p_i$（Gumbel-max 定理，可由 $P(\log p_i + g_i > \log p_j + g_j,\ \forall j)$ 积分证出）。指数分布的最小值是指数（竞速解释：每个类别是一场比赛，Gumbel 噪声等价于把概率变成「赢得比赛的概率」）。

**与 softmax 的关系**：对 log p + g 取 softmax 得到的「软化版本」就是可导代理——这正是 Gumbel-Softmax / Straight-Through 的核心：前向用 hard argmax（离散采样），反向用 soft softmax 近似梯度，解决「从离散分布无法反传」的问题。VAE 离散 latent、RL 离散动作、NAS 结构搜索全靠它。

**易错点**：1）$u$ 取 (0,1) 开区间，$\log(0)$ 溢出，要加 eps 或用 `1 - u`；2）数值上 log-域计算，p 为 0 的类别 log 报错；3）多个样本要独立噪声。

**复杂度**：$O(V)$ 采样（一次遍历 argmax），无需归一化——这是它对 multinomial（需前缀和）的优势：流式/分布式下更友好。

**追问**：Straight-Through 估计器为什么偏差（梯度是软近似而非真实）；温度 τ 在 Gumbel-Softmax 里控制什么（趋 0 变 hard、趋大趋均匀）。''',
        "keyPoints": [
            "argmax(log p_i + g_i)，g = -log(-log u)，精确等价按 p 采样",
            "无需归一化，O(V) 一次遍历，流式/并行友好",
            "softmax(log p + g) 是可导代理，构成 Gumbel-Softmax",
            "u 要落在开区间 (0,1)，防 log(0) 溢出",
            "ST-Gumbel 前向 hard 反向 soft，梯度是有偏近似",
        ],
        "followUps": [
            {"q": "Gumbel-Softmax 的温度 τ 起什么作用？", "a": "τ 缩放噪声与 logits：τ→0 输出逼近 onehot（梯度方差爆炸），τ 大时输出平滑（梯度稳但离散性差）。实践 τ 从 1 退火到 0.1~0.5，在可导性与离散性之间过渡。"},
        ],
        "code": {
            "lang": "python",
            "caption": "Gumbel-max 采样与分布等价性统计验证",
            "content": r'''import random
import math
from collections import Counter

def gumbel_sample(probs, rng):
    # argmax(log p + g)，g ~ Gumbel(0,1) = -log(-log u)
    best_i, best_v = 0, float('-inf')
    for i, p in enumerate(probs):
        if p <= 0:
            continue
        u = rng.random() * (1 - 1e-12) + 1e-12    # u 落在 (0,1)
        g = -math.log(-math.log(u))
        v = math.log(p) + g
        if v > best_v:
            best_i, best_v = i, v
    return best_i

if __name__ == '__main__':
    rng = random.Random(0)
    p = [0.5, 0.3, 0.2]
    n = 50000
    cnt = Counter(gumbel_sample(p, rng) for _ in range(n))
    for i in range(3):
        assert abs(cnt[i] / n - p[i]) < 0.02, (i, cnt[i] / n)
    # p 中含 0 的类别永远采不到
    cnt2 = Counter(gumbel_sample([0.7, 0.3, 0.0], rng) for _ in range(5000))
    assert 2 not in cnt2
    print('gumbel max ok, freq =', [round(cnt[i] / n, 3) for i in range(3)])''',
        },
    },

    {
        "id": "handcoded-040",
        "topic": "概率与采样",
        "type": "手撕",
        "difficulty": 2,
        "frequency": 2,
        "companies": ["快手", "字节", "阿里"],
        "years": ["2024"],
        "question": "手写按权重随机采样（轮盘赌：前缀和 + 二分），并与朴素线性扫描对比复杂度。",
        "answerMd": r'''**思路一句话**：把权重累积成前缀和数组（相当于把 [0, 总权重) 切成若干段），采样时 `u = rand() × total` 落在哪一段就选谁——二分定位 $O(\log n)$。

**为什么前缀和是对的**：u 均匀落在长度为 $w_i$ 的区间内概率 = $w_i/\sum w$，几何概率直接对应权重比例。`bisect_right(cum, u)` 返回第一个前缀和 > u 的下标，正是 u 所在段。

**实现要点**：1）构造 $O(n)$ 一次、采样 $O(\log n)$ 多次——权重静态时优于每次 $O(n)$ 的线性扫描轮盘赌；2）权重可为 0（长度为 0 的区间永远不会被命中，天然正确）；3）`u = random() * total` 落在 [0, total)，`bisect_right` 处理 u 恰好等于某前缀和的边界（概率 0，但实现要一致）。

**易错点**：1）每次采样后权重变化（如负采样去重）会让前缀和失效，要么重建要么用树状数组支持点更新 $O(\log n)$；2）浮点求和误差在权重极大极小混合时会偏——可用 `math.fsum` 或整数权重；3）要求 $O(1)$ 采样时用别名法（Alias Method）：构造 $O(n)$、采样 $O(1)$，两次随机（一个桶索引 + 一个桶内判断）。

**复杂度**：构造 $O(n)$ / 采样 $O(\log n)$；Alias 法采样 $O(1)$ / 空间 $O(n)$。

**应用**：推荐粗排按 eCPM 流量调控、强化学习按优先级回放（PER）、词负采样（word2vec 的 unigram^0.75 表本质是预缩放的轮盘赌）。''',
        "keyPoints": [
            "前缀和切段，u = rand·total 落段二分定位",
            "构造 O(n) / 采样 O(log n)，静态权重最优",
            "权重 0 的区间天然不会被命中",
            "权重动态变化要重建或换树状数组；O(1) 需求用别名法",
            "word2vec 负采样表 = 预缩放权重的轮盘赌",
        ],
        "followUps": [
            {"q": "别名法（Alias Method）的原理？", "a": "把权重乘 n 补齐成 n 个「平均高度」的桶，每个桶最多存两个类别（本桶 + 溢出类别），构造 O(n)；采样时先均匀选桶、再以桶内概率二选一，共 O(1)。空间 2n，适合超大词表高频采样。"},
        ],
        "code": {
            "lang": "python",
            "caption": "前缀和 + 二分的加权采样器",
            "content": r'''import random
import bisect
from collections import Counter

class WeightedSampler:
    def __init__(self, weights, seed=0):
        self.rng = random.Random(seed)
        self.cum = []
        total = 0
        for w in weights:
            assert w >= 0
            total += w
            self.cum.append(total)
        self.total = total

    def sample(self):
        u = self.rng.random() * self.total       # [0, total)
        return bisect.bisect_right(self.cum, u)  # u 落在哪段前缀

if __name__ == '__main__':
    ws = [1, 2, 3, 4]
    s = WeightedSampler(ws)
    n = 100000
    cnt = Counter(s.sample() for _ in range(n))
    for i, w in enumerate(ws):
        assert abs(cnt[i] / n - w / 10) < 0.01, (i, cnt[i] / n)
    zero = WeightedSampler([0, 1])               # 零权重永不命中
    assert all(zero.sample() == 1 for _ in range(1000))
    print('weighted sampler ok, freq =', [round(cnt[i] / n, 3) for i in range(4)])''',
        },
    },

    # ---------------------------------------------------------------- CV 手撕
    {
        "id": "handcoded-041",
        "topic": "CV 手撕",
        "type": "手撕",
        "difficulty": 2,
        "frequency": 5,
        "companies": ["Momenta", "地平线", "理想", "华为"],
        "years": ["2024", "2025"],
        "question": "手写 IoU（单框 + numpy 向量化批量版），处理不相交、包含、零面积等边界。",
        "answerMd": r'''**思路一句话**：$IoU = \frac{|A\cap B|}{|A\cup B|}$，交 = $\max(0,\min(x_2)-\max(x_1))\times\max(0,\min(y_2)-\max(y_1))$，并 = 两面积之和 − 交。

**易错点清单**：1）交的宽高必须是「右下取 min − 左上取 max」再裁 0（负值直接乘会算出正的假交集，两框分离时 x、y 同时为负负得正——经典翻车点）；2）面积计算前同样要保证框合法（$x_2\ge x_1$），退化框面积 0；3）并集为 0 时除零（两空框），返回 0 或加 eps；4）坐标格式：`(x1,y1,x2,y2)` 与 `(cx,cy,w,h)` 与 `(x,y,w,h)` 三种约定，转换别搞混；5）框可能是左上角坐标+宽高（YOLO 风格），交的算式完全不同。

**向量化版**：广播 `(N,1,4)` 与 `(1,M,4)`，一次算出 $N\times M$ 的 IoU 矩阵，检测评测/匹配（匈牙利分配前的代价矩阵）都用它；分母加 `1e-9` 防零。

**复杂度**：单对 $O(1)$；矩阵版 $O(NM)$ 时间、$O(NM)$ 空间（大集合要分块）。

**追问**：GIoU/DIoU/CIoU 差在哪（GIoU 补最小外接框解决不相交梯度为 0；DIoU 加中心距；CIoU 再加长宽比一致性）；IoU 阈值 0.5 的 mAP 为什么用多阈值。''',
        "keyPoints": [
            "交宽高 = min(右下) − max(左上)，必须裁负数为 0",
            "负负得正是最常见 bug：宽高分别 clamp 而不是乘积 clamp",
            "并 = A + B − 交，零并集除零防护",
            "确认坐标格式 (x1y1x2y2) vs (xywh) 再动手",
            "向量化用广播算 N×M 矩阵，分母加 eps",
        ],
        "followUps": [
            {"q": "GIoU 解决了 IoU 的什么问题？", "a": "两个不相交框 IoU 恒为 0，损失梯度为 0 无法优化。GIoU 引入最小外接框 C：GIoU = IoU − |C∖(A∪B)|/|C|，不相交时惩罚随外接框空隙增大，回归框能被「拉近」；DIoU/CIoU 再叠加中心点距离与长宽比项，收敛更快更准。"},
        ],
        "code": {
            "lang": "python",
            "caption": "IoU 标量版 + numpy 广播矩阵版",
            "content": r'''import numpy as np

def iou(a, b):
    # box: (x1, y1, x2, y2)
    iw = min(a[2], b[2]) - max(a[0], b[0])       # 交集宽（可为负）
    ih = min(a[3], b[3]) - max(a[1], b[1])
    inter = max(0, iw) * max(0, ih)              # 分别 clamp，防负负得正
    area_a = max(0, a[2] - a[0]) * max(0, a[3] - a[1])
    area_b = max(0, b[2] - b[0]) * max(0, b[3] - b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0

def iou_matrix(boxes_a, boxes_b):
    a = np.asarray(boxes_a, dtype=float)[:, None, :]     # (N,1,4)
    b = np.asarray(boxes_b, dtype=float)[None, :, :]     # (1,M,4)
    iw = np.clip(np.minimum(a[..., 2], b[..., 2]) - np.maximum(a[..., 0], b[..., 0]), 0, None)
    ih = np.clip(np.minimum(a[..., 3], b[..., 3]) - np.maximum(a[..., 1], b[..., 1]), 0, None)
    inter = iw * ih
    area_a = np.clip(a[..., 2] - a[..., 0], 0, None) * np.clip(a[..., 3] - a[..., 1], 0, None)
    area_b = np.clip(b[..., 2] - b[..., 0], 0, None) * np.clip(b[..., 3] - b[..., 1], 0, None)
    return inter / (area_a + area_b - inter + 1e-9)

if __name__ == '__main__':
    assert abs(iou((0, 0, 2, 2), (1, 1, 3, 3)) - 1 / 7) < 1e-9   # 交1并7
    assert iou((0, 0, 1, 1), (2, 2, 3, 3)) == 0.0                # 分离
    assert iou((0, 0, 2, 2), (0, 0, 2, 2)) == 1.0                # 自身
    assert iou((0, 0, 2, 2), (0, 0, 1, 1)) == 0.25               # 包含
    m = iou_matrix([(0, 0, 2, 2)], [(1, 1, 3, 3), (0, 0, 2, 2)])
    assert abs(m[0, 0] - 1 / 7) < 1e-6 and abs(m[0, 1] - 1.0) < 1e-6
    print('iou ok')''',
        },
    },

    {
        "id": "handcoded-042",
        "topic": "CV 手撕",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 5,
        "companies": ["Momenta", "地平线", "小鹏", "蔚来"],
        "years": ["2024", "2025"],
        "question": "手写 NMS 非极大值抑制（贪心版），输出保留框索引，并说明 soft-NMS 解决什么。",
        "answerMd": r'''**思路一句话**：按分数降序取最高分框保留，把它与剩余框逐个算 IoU，超过阈值的全部抑制；重复直到没有框——贪心保局部峰值。

**实现主线**：1）按分数排序得访问顺序；2）遍历：被抑制的跳过；未被抑制的进 keep，并把与它 IoU > thr 的框打抑制标记；3）keep 顺序天然是分数降序。

**易错点**：1）阈值判断是 `>` 还是 `>=`（约定问题，说清楚）；2）IoU 用的框格式与输入一致（xyxy），别把 (x,y,w,h) 直接喂进来；3）in-place 修改分数/列表会影响遍历（本实现用独立 suppressed 数组）；4）工程版用 numpy 向量化批量抑制 + 只保留 topk 候选（RPN 输出上万框时全两两比较 $O(n^2)$ 不可接受），或 CUDA NMS；5）class-agnostic 与 per-class NMS 的选择（多类同图是否互相抑制）。

**soft-NMS（必讲）**：贪心 NMS 在密集目标（重叠行人/车流）会把正确检测连同重叠框一起杀掉，召回掉。soft-NMS 不删除，而是把重叠框的分数衰减：$s_i \leftarrow s_i\cdot(1-IoU)$ 或高斯核 $s_i e^{-IoU^2/\sigma}$，最后按阈值截断——无训练成本，mAP 小涨。

**复杂度**：贪心两两比较 $O(n^2)$；向量化后均摊仍平方但常数小；GPU NMS 用 IoU 矩阵并行。''',
        "keyPoints": [
            "分数降序贪心：保留峰值、抑制 IoU 超阈值的其余框",
            "keep 顺序即分数降序，注意 > 与 >= 约定",
            "O(n^2) 两两比较，大规模用向量化/CUDA NMS + 前置 topk",
            "密集目标召回问题 → soft-NMS 分数衰减代替硬删除",
            "per-class 与 class-agnostic 按场景选择",
        ],
        "followUps": [
            {"q": "端到端检测器（DETR 系）为什么不需要 NMS？", "a": "DETR 用匈牙利一对一匹配 + object queries，训练目标就是「一个目标一个预测」，天然去重；后处理只剩阈值过滤。代价是收敛慢，后续 DINO/RT-DETR 用 query 去重和混合编码解决，工业部署省掉 NMS 的 CPU 瓶颈。"},
        ],
        "code": {
            "lang": "python",
            "caption": "贪心 NMS + 抑制关系自检",
            "content": r'''def nms(boxes, scores, iou_thr=0.5):
    # boxes: [(x1, y1, x2, y2)]；返回保留的索引（分数降序）
    def iou(a, b):
        iw = max(0, min(a[2], b[2]) - max(a[0], b[0]))
        ih = max(0, min(a[3], b[3]) - max(a[1], b[1]))
        inter = iw * ih
        ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
        return inter / ua if ua > 0 else 0.0

    order = sorted(range(len(boxes)), key=lambda i: -scores[i])
    suppressed = [False] * len(boxes)
    keep = []
    for i in order:
        if suppressed[i]:
            continue
        keep.append(i)
        for j in order:                       # 抑制与峰值重叠的框
            if j == i or suppressed[j]:
                continue
            if iou(boxes[i], boxes[j]) > iou_thr:
                suppressed[j] = True
    return keep

if __name__ == '__main__':
    boxes = [(0, 0, 10, 10), (1, 1, 11, 11), (20, 20, 30, 30), (21, 21, 31, 31)]
    scores = [0.9, 0.8, 0.7, 0.95]
    assert nms(boxes, scores, 0.5) == [3, 0]      # 高分组各留一个代表
    boxes2 = [(0, 0, 10, 10), (0.5, 0.5, 10.5, 10.5), (12, 0, 22, 10)]
    scores2 = [0.9, 0.95, 0.9]
    assert nms(boxes2, scores2, 0.5) == [1, 2]    # 重叠对保留高分
    assert nms([], []) == []
    print('nms ok')''',
        },
    },

    {
        "id": "handcoded-043",
        "topic": "CV 手撕",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["美团", "快手", "小红书"],
        "years": ["2024", "2025"],
        "question": "手写 KMeans（分配 + 更新两步迭代），处理空簇，并用 SSE 讲讲肘部法选 k。",
        "answerMd": r'''**思路一句话**：交替执行「分配」（每个点归最近中心）与「更新」（中心取簇内均值）直至分配不再变化——Lloyd 算法，目标函数（簇内 SSE）单调不增故必收敛。

**实现要点**：1）初始化随机取 k 个不同点；升级为 KMeans++（下一个中心按 $D(x)^2$ 概率采样）能显著改善聚类质量与稳定性，面试主动提；2）空簇处理：重新随机指派一个点（或取离自己中心最远的点），不处理会 NaN；3）收敛判据用「分配是否变化」比「中心移动量 < tol」更稳；4）距离用平方欧氏即可（比较不需要开根）。

**易错点**：1）只收敛到局部最优——多次随机重启取最小 SSE（sklearn 默认 n_init=10）；2）k 的选择：肘部法看 SSE-k 曲线拐点，或轮廓系数/Gap statistic；3）对量纲敏感，先标准化；4）大数据用 Mini-Batch KMeans（每次小批量更新中心，收敛快、近似质量）。

**复杂度**：每轮 $O(n\cdot k\cdot d)$，轮数与数据/初始化有关（通常几十轮）；总 $O(I\cdot n\cdot k\cdot d)$。$np$ 难精确最优，Lloyd 只是局部搜索。

**追问**：KMeans 为什么对初始值敏感（SSE 非凸）；和 GMM 的关系（KMeans 是等方差 GMM 的 EM 特例）；高维下为什么欧氏距离失效（维度灾难，改 cosine/ANNOY 召回）。''',
        "keyPoints": [
            "两步交替：最近中心分配 + 簇均值更新，SSE 单调不增必收敛",
            "KMeans++ 初始化（按 D^2 采样）+ 多次重启缓解局部最优",
            "空簇要重指派，否则均值 NaN",
            "肘部法/轮廓系数选 k；先做特征标准化",
            "每轮 O(n·k·d)，KMeans 是等方差 GMM 的 EM 特例",
        ],
        "followUps": [
            {"q": "KMeans 和 KMeans++ 初始化差在哪？", "a": "纯随机初始中心可能挤在一起，落进坏局部最优；KMeans++ 第一个中心随机选，之后每个新中心以正比于「到已选中心最小距离平方」的概率采样，把中心互相推开，理论上有 O(log k) 近似保证，实际收敛更快更稳。"},
        ],
        "code": {
            "lang": "python",
            "caption": "KMeans（Lloyd）+ 空簇处理 + SSE 自检",
            "content": r'''import random

def kmeans(points, k, iters=100, seed=0):
    rng = random.Random(seed)
    centers = list(rng.sample(points, k))          # 随机取 k 个不同点
    labels = [0] * len(points)
    def nearest(p):
        return min(range(k), key=lambda c: (p[0] - centers[c][0]) ** 2 +
                                            (p[1] - centers[c][1]) ** 2)
    for _ in range(iters):
        changed = False
        for idx, p in enumerate(points):           # 分配步
            c = nearest(p)
            if labels[idx] != c:
                labels[idx] = c
                changed = True
        for c in range(k):                         # 更新步
            members = [p for p, lb in zip(points, labels) if lb == c]
            if members:
                centers[c] = (sum(p[0] for p in members) / len(members),
                              sum(p[1] for p in members) / len(members))
            else:
                centers[c] = rng.choice(points)    # 空簇重指派
        if not changed:
            break
    sse = sum((p[0] - centers[lb][0]) ** 2 + (p[1] - centers[lb][1]) ** 2
              for p, lb in zip(points, labels))
    return labels, centers, sse

if __name__ == '__main__':
    pts = [(0, 0), (0, 1), (1, 0), (10, 10), (10, 11), (11, 10)]
    labels, centers, sse = kmeans(pts, 2)
    assert len(set(labels)) == 2
    assert labels[0] == labels[1] == labels[2]     # 前三个点同簇
    assert labels[3] == labels[4] == labels[5]     # 后三个点同簇
    assert labels[0] != labels[3]
    assert sse < 3.0, sse                          # 簇内紧凑
    print('kmeans ok, sse =', round(sse, 3), 'centers =', centers)''',
        },
    },

    {
        "id": "handcoded-044",
        "topic": "CV 手撕",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 4,
        "companies": ["拼多多", "美团", "快手"],
        "years": ["2024", "2025"],
        "question": "手写逻辑回归 + SGD 训练（数值稳定 sigmoid），在线性可分数据上收敛验证。",
        "answerMd": r'''**思路一句话**：模型 $p=\sigma(w^\top x+b)$，交叉熵损失对单个样本的梯度是极简的 $(p-y)x$ 与 $(p-y)$——SGD 逐样本更新 `w -= lr·(p−y)·x`。

**推导（必会）**：$L=-[y\log p+(1-y)\log(1-p)]$，$\sigma'(z)=\sigma(z)(1-\sigma(z))$，链式相消后 $\partial L/\partial z=p-y$。这个「预测减标签」的形式与 softmax 回归、MSE 的梯度结构同源，是手推题的标杆。

**数值稳定 sigmoid**：z≥0 时 $1/(1+e^{-z})$；z<0 时 $e^z/(1+e^z)$——避免 $e^{-z}$ 在 z 很负时上溢（fp64 之外的语言会直接 inf）。

**易错点**：1）SGD 要每个 epoch shuffle（样本顺序引入偏差）；2）学习率过大 sigmoid 饱和区梯度小反而慢/震荡，可加 L2（`w -= lr·(g·x + λw)`）；3）预测 `p>=0.5` 等价 `z>=0`，不用真算 sigmoid；4）类别不平衡时看 AUC/F1 而不是 accuracy；5）梯度消失不是问题（交叉熵配 sigmoid 恰好消掉 σ'），这是与 MSE 损失对比的核心优势。

**复杂度**：单样本 $O(d)$，一轮 $O(nd)$；可扩展成 mini-batch（方差与算力折中）。

**追问**：为什么交叉熵比 MSE 适合分类（MSE 配 sigmoid 梯度含 σ'，饱和区消失）；LR 为什么输出校准好（最大化似然天然匹配真实概率），这也是它长期当广告 ECPM 预估基线的原因。''',
        "keyPoints": [
            "梯度 = (p − y)：sigmoid 导数与交叉熵相消，极简形式",
            "sigmoid 分段式防 exp 上溢（z<0 走 e^z/(1+e^z)）",
            "SGD 每 epoch shuffle；可加 L2 正则",
            "预测阈值 p>=0.5 等价 z>=0",
            "CE 配 sigmoid 无饱和梯度问题，MSE 有",
        ],
        "followUps": [
            {"q": "MSE 损失配 sigmoid 会出什么问题？", "a": "梯度 ∂L/∂z = (p−y)·σ'(z)，σ' 在 |z| 大时趋 0——错得越离谱学得越慢（梯度消失）；交叉熵恰好把 σ' 消掉，错误越大梯度越大。这就是分类用 CE 不用 MSE 的根本原因。"},
        ],
        "code": {
            "lang": "python",
            "caption": "逻辑回归 + 逐样本 SGD，可分数据收敛验证",
            "content": r'''import random
import math

def sigmoid(z):
    if z >= 0:                            # 分段实现防 exp 上溢
        return 1 / (1 + math.exp(-z))
    e = math.exp(z)
    return e / (1 + e)

def train_logreg(X, y, lr=0.5, epochs=300, seed=0, l2=0.0):
    rng = random.Random(seed)
    d = len(X[0])
    w, b = [0.0] * d, 0.0
    for _ in range(epochs):
        idx = list(range(len(X)))
        rng.shuffle(idx)                  # 每个 epoch 打乱
        for i in idx:
            z = sum(wj * xj for wj, xj in zip(w, X[i])) + b
            g = sigmoid(z) - y[i]         # dL/dz = p − y
            for j in range(d):
                w[j] -= lr * (g * X[i][j] + l2 * w[j])
            b -= lr * g
    return w, b

def predict(X, w, b):
    return [1 if sum(wj * xj for wj, xj in zip(w, row)) + b >= 0 else 0 for row in X]

if __name__ == '__main__':
    data = [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [0.5, 0.4],
            [1.0, 1.0], [2.0, 1.0], [1.5, 1.5], [2.0, 2.0]]
    labels = [0, 0, 0, 0, 1, 1, 1, 1]
    w, b = train_logreg(data, labels)
    assert predict(data, w, b) == labels
    assert sigmoid(0) == 0.5 and abs(sigmoid(1000) - 1) < 1e-12 and sigmoid(-1000) >= 0
    print('logreg ok, w =', [round(x, 2) for x in w], 'b =', round(b, 2))''',
        },
    },

    {
        "id": "handcoded-045",
        "topic": "CV 手撕",
        "type": "手撕",
        "difficulty": 4,
        "frequency": 4,
        "companies": ["华为", "Momenta", "地平线", "小米"],
        "years": ["2024", "2025"],
        "question": "用 numpy 手写卷积前向传播（四重循环朴素版），支持 stride/padding，并用脉冲输入验证权重切片对齐。",
        "answerMd": r'''**思路一句话**：输出每个位置 = 输入上对应感受野 patch 与卷积核逐元素乘求和加偏置；四重循环 `N/F/Ho/Wo` 最直观，尺寸公式 $H_o=\lfloor (H+2p-K)/s \rfloor + 1$。

**实现要点**：1）先 `np.pad` 空间维（通道不 pad）；2）stride 时窗口起点 `i*stride`；3）输出形状推导是面试官盯着的点，写代码前先说公式；4）脉冲自检：全零图只在 (ch=1, r=2, c=2) 放 1，则输出 (2,2) 位置应等于 `w[:, 1, 1, 1] + b`——一行代码验证所有下标对齐，比肉眼检查强得多。

**易错点**：1）pad 是 pad 在 H/W 两头各 p，通道和 batch 维 pad 0；2）除法整除：$H+2p-K$ 不被 s 整除时向下取整（PyTorch 同），说清 ceil 模式（same padding）的差别；3）`(patch * w[f]).sum()` 是逐元素乘再求和，不是矩阵乘；4）多通道输入时 patch 是 `(C, K, K)` 三维，别只切空间维。

**复杂度**：朴素 $O(N F H_o W_o C K^2)$；实际框架用 im2col/Winograd/FFT：im2col 把卷积变 GEMM 借 cuDNN 优化，Winograd 对 3×3 省约 2 倍乘法，是「为什么手写版慢、工程版快」的答案。

**追问**：反向传播怎么算（对输入是转置卷积/相关、对权重是 patch 与上游梯度的相关求和）；depthwise conv 和普通 conv 的区别。''',
        "keyPoints": [
            "输出尺寸 Ho = (H + 2p − K) // s + 1",
            "pad 只 pad 空间维；先 pad 后切窗口",
            "脉冲输入自检下标对齐：单点输入的输出 = 对应位置核切片 + bias",
            "朴素 O(N·F·Ho·Wo·C·K^2)，工程用 im2col+GEMM / Winograd",
            "stride 不整除时向下取整（与 PyTorch 一致）",
        ],
        "followUps": [
            {"q": "im2col 为什么快？", "a": "把每个感受野 patch 展开成一行拼成矩阵，卷积变成一次大 GEMM：内存访问规整、复用 BLAS/cuDNN 极致优化的 kernel，代价是空间膨胀 K^2 倍。Winograd 则从数学上减少乘法次数（3×3 s=1 省 2.25 倍乘法），小卷积核常用。"},
        ],
        "code": {
            "lang": "python",
            "caption": "numpy 卷积前向（stride/padding）+ 脉冲对齐自检",
            "content": r'''import numpy as np

def conv2d_naive(x, w, b, stride=1, pad=0):
    # x: (N, C, H, W)，w: (F, C, KH, KW)，b: (F,)
    N, C, H, W = x.shape
    F, _, KH, KW = w.shape
    Ho = (H + 2 * pad - KH) // stride + 1
    Wo = (W + 2 * pad - KW) // stride + 1
    xp = np.pad(x, ((0, 0), (0, 0), (pad, pad), (pad, pad)))
    out = np.zeros((N, F, Ho, Wo))
    for n in range(N):
        for f in range(F):
            for i in range(Ho):
                for j in range(Wo):
                    hs, ws = i * stride, j * stride
                    patch = xp[n, :, hs:hs + KH, ws:ws + KW]
                    out[n, f, i, j] = (patch * w[f]).sum() + b[f]
    return out

if __name__ == '__main__':
    rng = np.random.default_rng(0)
    x = rng.normal(size=(2, 3, 5, 5))
    w = rng.normal(size=(4, 3, 3, 3))
    b = rng.normal(size=4)
    out = conv2d_naive(x, w, b, stride=1, pad=1)
    assert out.shape == (2, 4, 5, 5)             # pad=1 尺寸不变
    out2 = conv2d_naive(x, w, b, stride=2, pad=0)
    assert out2.shape == (2, 4, 2, 2)            # (5-3)//2+1 = 2
    # 脉冲自检：单点输入对应的输出 = 核切片 + bias
    x1 = np.zeros((1, 3, 5, 5))
    x1[0, 1, 2, 2] = 1.0
    o = conv2d_naive(x1, w, b, stride=1, pad=1)
    assert np.allclose(o[0, :, 2, 2], w[:, 1, 1, 1] + b)
    print('conv2d ok')''',
        },
    },

]

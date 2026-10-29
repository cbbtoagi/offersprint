# -*- coding: utf-8 -*-
# 后训练与对齐题库（纯数据文件，顶部不 import）
# 覆盖：SFT / PEFT / RLHF 全流程 / 直接对齐(DPO系) / GRPO与推理对齐 / 蒸馏与迭代 / 评测与安全 / 工程选型

QUESTIONS = [
    # ---------------------------------------------------------------- SFT
    {
        "id": "posttrain-001",
        "topic": "SFT",
        "type": "八股",
        "difficulty": 3,
        "frequency": 5,
        "companies": ["字节", "阿里", "智谱", "百度"],
        "years": ["2023", "2024", "2025"],
        "question": "SFT 的指令数据一般怎么构建和清洗？说说你实际做数据时的完整 pipeline。",
        "answerMd": r'''**一句话核心**：指令数据 pipeline 是「采集/生成 → 清洗去重 → 质量打分 → 多样性配比 → 人工抽检」的漏斗，数据质量与多样性比数量更重要，且每一环都要有可量化的过滤标准。

**1. 来源与生成。** 采集：开源指令集（Alpaca/ShareGPT 类）、业务日志（需脱敏合规）、人工标注。生成：self-instruct 用强模型自举扩展种子任务；evol-instruct 沿难度（加约束、多步推理）和维度（改写、增广）做指令进化；对代码/数学用「题目 + 可执行校验」反向生成保证可验证。

**2. 清洗与去重。** 规则层：长度过滤、语言检测、乱码/模板残留、敏感内容；语义层：embedding 召回 + 聚类去近似重复，exact/near-dedup 分开做；对第三方开源数据要做 license 和污染检查（与评测集 n-gram 重叠）。

**3. 质量打分。** 用强模型做 judge：按正确性、完整性、指令遵循、无害性多维打分，低分剔除或重写；保留低分但任务类型稀缺的样本防止分布塌缩。可用「IFD 类指标」衡量指令与回答的信息增益，过滤答非所问。

**4. 配比与抽检。** 按任务簇（问答/写作/代码/数学/工具调用/安全拒答）控制配比，域内数据要掺通用数据防遗忘；最后分层抽样人工盲评，建立数据卡片记录每批来源与指标，保证可回溯可迭代。''',
        "keyPoints": [
            "漏斗：生成/采集 → 规则清洗 → 语义去重 → 模型打分 → 配比 → 人工抽检",
            "self-instruct/evol-instruct 扩量，可验证任务反向生成保正确性",
            "去重分 exact 与 near（embedding 聚类），并做评测污染检查",
            "按任务簇配比，域内数据掺通用防遗忘，数据可回溯",
        ],
        "followUps": [
            {"q": "怎么判断该补哪类数据？", "a": "用分类器给全量数据打任务簇标签看分布，再对评测集按能力分桶找短板；也可用 loss 在各簇上的表现定位学不好的类型，针对性补数比全局加量更有效。"},
        ],
    },
    {
        "id": "posttrain-002",
        "topic": "SFT",
        "type": "八股",
        "difficulty": 2,
        "frequency": 3,
        "companies": ["智谱", "阿里", "面壁智能"],
        "years": ["2023", "2024"],
        "question": "怎么理解 LIMA 说的「1K 高质量样本就够」？质量和数量到底怎么权衡？",
        "answerMd": r'''**一句话核心**：LIMA 用约一千条精心挑选的高质量回答微调 LLaMA 就获得不错的对齐效果，说明指令微调主要是在「激发」预训练里已有的知识与能力，对齐阶段学的关键是对的行为格式与风格；但它的上限受限于底座能力，并非数据越少越好。

**1. LIMA 的主张。** 以质量优先：来源上选论坛高赞回答、百科与人工撰写，统一风格、覆盖面广但每类样本精挑；不做 RLHF。结果在很多真实 prompt 上与 RLHF 模型难分伯仲，由此提出 superficial alignment hypothesis：对齐是表层的，预训练已把能力注入，SFT 只需教会「何时、以何种格式输出」。

**2. 怎么正确理解。** 它证明的是「小而精的上界不低」，不是「大规模数据无用」：底座越强需要的对齐数据越少；但复杂能力（长推理、工具调用、多语言）仍需更大量更多样数据，后续工作（如对数据质量做过滤再扩规模）普遍显示质量和数量都要抓——先提纯再扩量，而不是二选一。

**3. 实践权衡。** 预算小、底座强：几百到几千条精品数据 + 严格格式统一即可；要覆盖长尾任务、业务域：在质量过滤后扩到几十万级；判据是评测增益是否饱和——同分布数据翻倍带来的边际收益趋近零时，应转向补多样性而不是继续堆量。''',
        "keyPoints": [
            "LIMA：约 1K 精选样本 + LLaMA 底座即获对齐效果",
            "superficial alignment：SFT 主要激发与格式化预训练能力",
            "上限受底座能力约束，复杂能力仍需规模化数据",
            "实践：先质量过滤再扩量，看评测增益是否饱和",
        ],
        "followUps": [
            {"q": "强底座上少量数据的 SFT 有什么明显短板？", "a": "长尾任务覆盖差、指令多样性不足时容易在未见过的指令格式上失稳；另外小数据易过拟合到固定风格，输出多样性下降，通常靠混入通用对话数据和低学习率缓解。"},
        ],
    },
    {
        "id": "posttrain-003",
        "topic": "SFT",
        "type": "八股",
        "difficulty": 3,
        "frequency": 5,
        "companies": ["字节", "阿里", "月之暗面", "DeepSeek"],
        "years": ["2023", "2024", "2025"],
        "question": "多轮对话的 SFT 训练时，chat template 和 loss mask 是怎么处理的？有哪些容易踩的坑？",
        "answerMd": r'''**一句话核心**：多轮样本按模板渲染成一条序列，loss 只算 assistant 回复段（label 其余位置置 -100），多轮中每个 assistant 轮都要计 loss；最大的坑是训练与推理模板不一致，以及模板边界 token（eos、起始符）该不该计 loss 处理错。

**1. 模板与序列化。** 每条多轮对话按 chat template 拼成 system/user/assistant 交替的单条 token 序列，特殊 token（角色头、eos）进词表；长对话截断时从整轮边界截，避免半轮损坏语义。

**2. loss mask 规则。** prompt 侧（system、user、角色标记）label 置 -100；每个 assistant 轮的回复 token 计 loss——多轮对话等价于把每个 assistant 轮当作独立的续写任务一次性联合训练，上下文共享，效率比单轮拆样本高。回复末尾的 eos 一般计 loss（否则模型学不会停）；生成提示（如 <assistant> 头部）不计。

**3. 常见坑。** 一是训练/推理模板不一致：空格、换行、system 是否并入 user、few-shot 位置，差一个 token 都会让下游效果明显掉，训练推理必须走同一套渲染代码；二是 eos 处理：有的模板在 assistant 后还会拼下一轮起始符，diff 式计算 span 时容易把边界算进去；三是截断把 eos 截掉导致输出不停；四是 tool call 轮 role 更多，mask 规则要先在模板层面定义清楚。

**4. 一条经验。** 上线前做「模板一致性单测」：把训练样本渲染出的 token 序列与推理时同 prompt 的前缀逐 token 对比，一致才放行。''',
        "keyPoints": [
            "label 只算 assistant 段，-100 屏蔽 prompt 侧",
            "多轮每条 assistant 轮都计 loss，联合训练效率高",
            "eos 要计 loss 否则学不会停止；截断保整轮",
            "训练推理必须同模板，边界 token 是事故高发区",
            "上线前做模板一致性单测",
        ],
        "followUps": [
            {"q": "多轮对话只算最后一轮 loss 有什么问题？", "a": "监督信号大量浪费，早轮回复完全没学；且模型对多轮上下文里的自身历史没有直接训练信号，长对话一致性会变差。除非只关心最终轮能力的特定任务，一般都全轮计 loss。"},
        ],
    },
    {
        "id": "posttrain-004",
        "topic": "SFT",
        "type": "八股",
        "difficulty": 3,
        "frequency": 4,
        "companies": ["字节", "美团", "百川智能"],
        "years": ["2024", "2025"],
        "question": "全参数微调和轻量微调（LoRA 等）怎么选？各自的适用边界在哪？",
        "answerMd": r'''**一句话核心**：数据量大（十万级以上）、任务与通用能力差异大、算力充足选全参；数据少、要快速迭代、显存受限或多任务隔离部署选 LoRA 系；底座能力是天花板，两者上限差距随数据质量提高而缩小。

**1. 全参微调。** 更新全部权重，表达能力强，对「领域语言、复杂格式、长推理行为」的重塑更彻底；代价是显存（优化器状态约 16 字节/参数）、灾难性遗忘风险更高、每任务一份完整权重不好管理。适合底座与目标差异大的场景，比如从基座到垂直行业模型。

**2. 轻量微调。** LoRA 冻结主干只训低秩增量，显存和存储小一个量级、训练稳定、可多 adapter 复用同一底座；缺点是容量受秩限制，对大幅改变行为模式的任务（注入新知识、切换语言、超长 CoT 风格）可能不够。适合风格对齐、格式约束、分类器化小任务和多业务线隔离。

**3. 决策要素。** 看四点：数据规模（<1 万基本 LoRA 足够）、任务差异（改知识 vs 改行为）、算力预算、部署约束（是否要一个底座挂多个业务）。折中方案很常见：全参低学习率 + 混通用数据，或者 MLP 层全参 + 注意力 LoRA。

**4. 一个误区。** 「全参一定优于 LoRA」在同等数据质量下未必成立，尤其小数据全参更容易过拟合和遗忘；先用 LoRA 打基线再决定是否升级全参，是性价比最高的流程。''',
        "keyPoints": [
            "大数据 + 大域差 + 算力足 → 全参；小数据快迭代 → LoRA",
            "全参：表达力强但显存高、遗忘风险大",
            "LoRA：容量受秩限制，改行为够用、注知识偏弱",
            "决策看数据规模/任务差异/算力/多业务隔离四要素",
            "先用 LoRA 打基线，再评估全参收益",
        ],
        "followUps": [
            {"q": "LoRA 微调效果明显不如全参，最可能的原因是什么？", "a": "一是任务需要注入新知识或大幅改变输出分布，低秩容量不够；二是秩/alpha 或作用模块太少（只挂了 q_proj）；三是学习率没适配。可以先加大秩、扩展到全部线性层，再考虑全参。"},
        ],
    },
    {
        "id": "posttrain-005",
        "topic": "SFT",
        "type": "八股",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["阿里", "快手", "零一万物"],
        "years": ["2024", "2025"],
        "question": "垂直领域微调后模型通用能力明显下降，怎么办？聊聊灾难性遗忘的成因和对策。",
        "answerMd": r'''**一句话核心**：灾难性遗忘源于后训练分布变窄、参数被少量数据大幅拉离预训练解；对策核心是「掺通用数据回放 + 控制更新幅度」，再配合 LoRA、低学习率与正则化手段。

**1. 成因。** SFT 数据分布窄（领域问答为主），交叉熵在窄分布上优化会把共享参数推向只拟合该分布的解，通用能力对应的行为模式被覆写；学习率过高、epoch 过多、数据同质化都会加剧。另一种是「能力还在但不再表达」：安全/格式等先验被新模板覆盖。

**2. 数据层对策（最有效）。** 混合通用指令数据回放，常见域内：通用在 1:1 到 1:5 之间按实验扫；通用数据选高质量多样本源，覆盖语言、推理、代码、写作；领域数据本身做多样性增强，避免千篇一律的模板。

**3. 训练层对策。** 降学习率（比通用 SFT 更小）、减少 epoch、warmup + cosine；LoRA 天然限制参数漂移，遗忘显著更小；全参时可用权重正则（对齐到初始权重的 L2/EWC 思想）或前后训练阶段的权重插值。

**4. 评测闭环。** 必须同时监控领域指标和通用基准（MMLU 类、通用对话、代码、数学），画「领域增益 vs 通用损失」曲线找平衡点；如果领域收益小、通用损失大，优先怀疑数据质量而不是继续调参。''',
        "keyPoints": [
            "成因：窄分布 + 更新幅度大把参数拉离通用解",
            "首选数据回放：域内与通用按比例混合（常 1:1~1:5）",
            "训练层：低 LR、少 epoch、LoRA 限漂移、正则化",
            "评测要领域与通用双轨，找增益-损失平衡点",
        ],
        "followUps": [
            {"q": "通用数据回放的比例怎么定？", "a": "没有定数，从小比例起步网格扫，观察通用基准恢复但领域指标不掉的拐点；也可以按 loss 权重而非样本数控制，或两阶段训练（先领域后混合退火）让终点落在混合分布上。"},
        ],
    },
    {
        "id": "posttrain-006",
        "topic": "SFT",
        "type": "八股",
        "difficulty": 3,
        "frequency": 4,
        "companies": ["字节", "DeepSeek", "MiniMax"],
        "years": ["2024", "2025"],
        "question": "SFT 的关键超参怎么设？学习率、epoch、batch size 各有什么讲究，过拟合有哪些信号？",
        "answerMd": r'''**一句话核心**：SFT 超参的量级是「小学习率 + 少 epoch + 适中 batch」：7B 全参 LR 约 1e-5 量级（比预训练小一个量级以上），epoch 1~3，LoRA 可用大 5~10 倍的 LR；过拟合信号看 eval loss 回升、回复变长或变短僵化、通用基准下滑。

**1. 学习率。** 全参：7B~14B 常在 5e-6 到 2e-5，随模型增大递减，warmup 3%~10% 后 cosine 衰减；LoRA/QLoRA：因可训练参数少，常用 1e-4 量级。判断标准是小数据快速收敛不过冲：梯度爆炸或 loss 震荡就降。

**2. epoch 与数据规模。** 1 万~10 万条高质量数据通常 2~3 个 epoch 封顶；数据百万级或混了大量预训练式数据时 1 个 epoch 即可。重复太多 epoch 是过拟合与风格僵化的最大来源，宁可加数据不加 epoch。

**3. batch size。** 全局 batch 按对话条数 32~128 常见；太小梯度噪声大、太大泛化变差且样本利用率低，可配合较小 LR。有效 batch 受显存约束时用梯度累积；序列打包后要按 token 重新校准。

**4. 过拟合信号。** eval loss 先降后升是经典信号；更隐蔽的行为信号：输出开始复读模板、长度分布突变（显著变长或变短）、多样性指标下降、通用能力评测下滑、对改写过的指令泛化变差。对策：早停、降 epoch、加数据多样性、加正则或回放数据。''',
        "keyPoints": [
            "全参 7B 级 LR 5e-6~2e-5，LoRA 用 1e-4 量级",
            "epoch 1~3，大数据 1 epoch，加数据优于加 epoch",
            "全局 batch 数十条对话，梯度累积补显存",
            "过拟合信号：eval loss 回升、模板复读、长度突变、通用下滑",
        ],
        "followUps": [
            {"q": "warmup 在 SFT 里为什么重要？", "a": "微调初期权重已在一个好的解附近，大 LR 冷启动容易把参数推离造成不可逆损伤；warmup 让初始几步小步试探，稳定 adam 二阶矩估计，之后按 cosine 衰减平滑收敛。"},
        ],
    },
    {
        "id": "posttrain-007",
        "topic": "SFT",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["字节", "快手"],
        "years": ["2024", "2025"],
        "question": "手写：多轮对话 SFT 的编码函数，对 user/system 部分做 loss mask，只对 assistant 回复计 loss。",
        "answerMd": r'''**一句话核心**：逐轮渲染模板、用「与上一轮渲染结果的长度差」定位每轮新增 token，assistant 轮的新增段保留 label、其余置 -100；边界 eos 的取舍要在模板层面明确。

**实现要点。** 一是复用 tokenizer 的 apply_chat_template 保证训练推理模板一致；二是用增量 diff 而不是手写角色头拼接，避免与模板实现不一致；三是注意 assistant 轮渲染结果的尾部可能包含 eos 与下一轮起始符，按模板语义决定哪些计入 loss（通常 eos 计、下一轮起始符不计）。

**复杂度与正确性。** 逐轮重渲染的代价是每轮一次模板调用，整体 $O(T^2)$ 的字符串拼接量级，对几十轮内的对话完全可接受；若要做超长对话优化，可改为只在模板含全局结构时才重渲染。验证正确性的两个断言必须写进单测：labels 中非 -100 的位置集合恰好等于所有 assistant 段；把 labels 解码回去应还原出全部回复文本而不含角色头。截断发生在样本级：超长时从最早轮开始丢弃，并保证最后一轮是完整 assistant 轮且以 eos 结尾。''',
        "keyPoints": [
            "逐轮 apply_chat_template，用长度差定位新增 token",
            "assistant 新增段计 loss，其余置 -100",
            "eos 计 loss、下一轮起始符通常不计，需按模板定义",
            "训练与推理共用同一渲染函数防模板漂移",
        ],
        "followUps": [
            {"q": "这种 diff 写法在什么情况下会出错？", "a": "模板含 per-message 不可缓存的全局结构时（如总轮数计数、日期注入），逐轮重渲染的新增段不等于真实拼接；以及 assistant 轮尾部带下一轮起始符时会把非回复 token 误计 loss，需要按模板把边界单独处理。"},
        ],
        "code": {
            "lang": "python",
            "caption": "多轮对话编码与 loss mask",
            "content": '''import torch

def encode_multiturn(messages, tokenizer):
    """逐轮渲染 chat 模板，仅对 assistant 新增 token 计 loss。
    messages: [{"role": "user"/"assistant"/"system", "content": str}, ...]
    """
    input_ids, labels = [], []
    prev_len = 0
    history = []
    for msg in messages:
        history.append(msg)
        # 每轮重渲染完整对话，长度差即该轮新增 token
        full = tokenizer.apply_chat_template(history, tokenize=True)
        seg = full[prev_len:]
        input_ids.extend(seg)
        if msg["role"] == "assistant":
            labels.extend(seg)          # 回复段计 loss（含尾部 eos）
        else:
            labels.extend([-100] * len(seg))  # prompt 段屏蔽
        prev_len = len(full)
    return torch.tensor(input_ids), torch.tensor(labels)

# loss 计算时：
# loss = F.cross_entropy(logits[:, :-1].transpose(1, 2),
#                        labels[:, 1:], ignore_index=-100)'''
        },
    },
    {
        "id": "posttrain-008",
        "topic": "SFT",
        "type": "场景",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["美团", "拼多多", "小红书"],
        "years": ["2024", "2025"],
        "question": "业务方给你 5 万条客服领域对话，要求微调一个 8B 模型上线，你怎么设计方案并验证效果？",
        "answerMd": r'''**一句话核心**：先做数据体检与任务定义，选「LoRA 打基线 + 混通用数据防遗忘」的保守方案，离线用领域评测集与通用基准双轨验证，灰度上线看业务指标，最后评估是否升级全参。

**1. 数据先行。** 抽样 500 条人工看质量：答对率、格式、是否覆盖真实业务分支；聚类看任务分布，砍掉低质与重复；补关键短板（多轮澄清、转人工、拒答边界），并按模板统一改写。5 万条对 8B 是充足但未必干净的量，清洗后可能剩 3 万。

**2. 训练方案。** 基线一：LoRA（r=16~64、挂全部线性层）、LR 1e-4 量级、2 epoch；基线二：全参低 LR 1e-5、掺 20%~50% 通用对话数据。以基线一为主，因为它迭代快、遗忘小、可多业务共存。

**3. 离线评测。** 构建领域评测集（真实分支各留样本、含对抗与边界 case），用 LLM-judge + 人工抽检双通道；同时跑通用能力基准与安全拒答集，量化遗忘与过度拒答。指标不达标先回数据而不是调超参。

**4. 上线与迭代。** 灰度 5%~10% 流量，看解决率、转人工率、满意度与平均轮次；收集线上 badcase 进入下一轮数据迭代。若 LoRA 与全参差距 > 2 个点且数据质量已确认，再投入全参。''',
        "keyPoints": [
            "先数据体检：质量抽样、聚类去重、补短板与边界",
            "LoRA 打基线 + 掺通用数据，全参作为后备升级",
            "双轨评测：领域评测集 + 通用/安全基准防遗忘",
            "灰度看业务指标，badcase 回流形成数据迭代闭环",
        ],
        "followUps": [
            {"q": "如果业务只关心解决率，还要看通用基准吗？", "a": "要。通用能力下滑常以隐蔽方式伤害业务：多轮理解变差、异常输入处理崩坏、安全风险上升，最终反噬解决率；至少保留一份小型通用回归集作为发布门禁。"},
        ],
    },
    {
        "id": "posttrain-009",
        "topic": "SFT",
        "type": "八股",
        "difficulty": 4,
        "frequency": 4,
        "companies": ["DeepSeek", "智谱", "月之暗面", "面壁智能"],
        "years": ["2025", "2026"],
        "question": "推理模型出来之后，SFT 阶段的做法有什么变化？长思维链数据怎么用？",
        "answerMd": r'''**一句话核心**：SFT 从「教答案风格」升级为「教推理轨迹」：用强推理模型蒸馏长 CoT 轨迹做冷启动或直接蒸馏小模型，数据要带反思、验证、回溯等行为；同时更强调保留通用能力的混合配比，以及与 RL 阶段的衔接。

**1. 数据形态变化。** 传统 SFT 是问答式短回复；推理时代的 SFT 样本变成带结构化思维链的长轨迹：问题分析、尝试、自我校验（wait/check/verify 类转折）、修正后给出最终答案；数学代码类要答案可验证。质量门槛从「答案对」变成「过程对且轨迹干净」，含冗余复读、格式混乱的轨迹要清洗。

**2. 两种用法。** 一是冷启动：给基座灌数千到数万条长 CoT，让 RL 阶段从可读、格式稳定的状态出发（R1 的 cold start 思路）；二是蒸馏：把强模型的轨迹直接微调小模型，小模型在数学代码上能获得大幅提升，性价比高于自己跑 RL——但蒸馏学到的是模仿输出分布，能力上限一般低于自跑 RL 的学生。

**3. 配比与防坍缩。** 长 CoT 数据占比过高会让小问题也「过度思考」，输出冗长、延迟变高；要混入短回复、非推理任务数据控制思考行为，或用「按难度路由思考长度」的数据课程。2025 年以来的普遍配方是 SFT 冷启动 + RLVR 主训练 + 通用 RL 对齐的管线，SFT 定位从对齐主力变为管线中的一环。''',
        "keyPoints": [
            "SFT 样本从问答变为带反思/验证的长推理轨迹",
            "两种角色：RL 冷启动数据 + 直接蒸馏小模型",
            "轨迹质量门槛：过程正确、格式干净、可验证",
            "混短回复防过度思考，思考长度按难度分层",
            "R1 后 SFT 定位变成管线一环而非对齐主力",
        ],
        "followUps": [
            {"q": "蒸馏轨迹里模型「假装反思」怎么办？", "a": "轨迹里出现固定套路的 wait/let me think 但不产生信息增量，属于风格模仿；可用轨迹级过滤（检查转折后是否真的改变结论、剔除复读段），或用过程奖励模型对推理步打分筛选有效反思。"},
        ],
    },
    # ---------------------------------------------------------------- PEFT
    {
        "id": "posttrain-010",
        "topic": "PEFT",
        "type": "八股",
        "difficulty": 4,
        "frequency": 5,
        "companies": ["字节", "阿里", "腾讯", "NVIDIA"],
        "years": ["2023", "2024", "2025"],
        "question": "讲讲 LoRA 的原理，为什么低秩增量是有效的？秩 r 怎么选？",
        "answerMd": r'''**一句话核心**：LoRA 假设微调时权重更新具有低本征秩，用 $W' = W + \frac{\alpha}{r}BA$（$A \in \mathbb{R}^{r \times d}$、$B \in \mathbb{R}^{d_{out} \times r}$，B 初始为零）把可训练参数从 $d_{out} \times d_{in}$ 降到 $(d_{out}+d_{in})r$；秩按任务复杂度从 8 到 256 起，关键看「加多大容量能让评测饱和」。

**1. 原理。** 冻结预训练权重 $W$，学习低秩分解的增量：前向 $\frac{\alpha}{r} BAx$，$A$ 用高斯/Kaiming 初始化、$B$ 置零，保证训练起点等价原模型；缩放 $\alpha/r$ 让调秩时学习率不必重调。梯度只流过 $A、B$，优化器状态与梯度显存大幅下降，主干可以 offload 或量化。

**2. 为什么低秩有效。** 经验观察是微调的更新矩阵本征秩很低（原论文在下游任务上 $r=1\sim4$ 就能竞争），因为适配一个任务通常只需在少数「方向」上调整表征；大模型预训练学到的通用表征冗余度高，任务适配是低维流形上的小移动。注意「低秩」是对每个权重矩阵而言，整体能力还来自大量矩阵各自的低秩更新叠加。

**3. 秩选择。** r=8~16 是风格/格式类任务起点；领域差异大、注入知识、多任务共享 adapter 时升到 64~256；alpha 常取 r 的 1~2 倍。选择标准是看验证集增益是否随 r 饱和，同时监控过拟合：r 过大、数据少时更易过拟合。''',
        "keyPoints": [
            r"$W' = W + (\alpha/r)BA$，B 零初始化保证起点等价",
            "依据：微调更新矩阵本征秩低，任务适配是低维调整",
            "可训练参数与优化器状态降几个数量级",
            "r=8~16 起步，域差大升到 64~256，以验证集饱和为准",
        ],
        "followUps": [
            {"q": "LoRA 训练时 B 零初始化有什么副作用？", "a": "初始梯度只在 A 侧流动，B 从零开始，早期有效学习率偏低、两个矩阵的学习进度不对称；一般无碍，但对很小数据集可考虑非对称初始化替代方案（如 PiSSA/OLoRA 类），或适当加长 warmup。"},
        ],
    },
    {
        "id": "posttrain-011",
        "topic": "PEFT",
        "type": "八股",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["字节", "智谱", "华为"],
        "years": ["2024", "2025"],
        "question": "LoRA 应该加在模型的哪些模块上？只加 attention 够吗？",
        "answerMd": r'''**一句话核心**：经验结论是把 LoRA 加到所有线性投影（attention 的 q/k/v/o 与 MLP 的 gate/up/down）效果最好，只加 q/v 是早期算力受限的折中；预算有限时优先覆盖 MLP，它承担大量任务知识适配。

**1. 早期做法与演进。** 原 LoRA 论文在注意力上做消融，发现 $W_q$ 与 $W_v$ 单独加效果较好，于是「只加 q_proj/v_proj」一度成为默认配置；后续复现（QLoRA 论文等）系统比较后确认：同等参数预算下，覆盖所有线性层的低秩设置优于只覆盖注意力的高秩设置。

**2. 为什么 MLP 重要。** FFN 的 up/down/gate 投影与事实知识、领域词元的读写强相关；任务适配往往需要改「特征组合方式」，这主要发生在 MLP。只调注意力的 LoRA 通常表现为「学到了格式和风格，学不进新知识」。

**3. 工程细节。** 现代模型有 GQA/MoE：GQA 下 k/v 投影输出维变小，注意 LoRA 形状按实际层配置生成；MoE 层专家数量多，可只挂共享层或按路由热度选择性挂；embedding/lm_head 一般不动（词表大、容易过拟合），除非分词器变了。预算分配上，用「低秩 + 全线性层」替换「高秩 + 少数层」是普遍更优的默认。''',
        "keyPoints": [
            "全线性层（attn q/k/v/o + MLP gate/up/down）效果最好",
            "只加 q/v 是旧默认，同等预算下不如低秩全覆盖",
            "MLP 承担知识类适配，缺失时学不进新知识",
            "GQA/MoE 下按层实际形状挂载，embedding 一般不动",
        ],
        "followUps": [
            {"q": "embedding 或 lm_head 需要训练的情形有哪些？", "a": "新增特殊 token、换词表、扩充语言时必须训 embedding（可只训新增行）；输出分布与预训练差异极大的任务（如受限文法生成）有时放开 lm_head，但要配小学习率防过拟合。"},
        ],
    },
    {
        "id": "posttrain-012",
        "topic": "PEFT",
        "type": "八股",
        "difficulty": 4,
        "frequency": 5,
        "companies": ["字节", "阿里", "NVIDIA", "智谱"],
        "years": ["2023", "2024", "2025"],
        "question": "QLoRA 是怎么把 65B 模型微调塞进单卡的？NF4 和双量化分别解决什么问题？",
        "answerMd": r'''**一句话核心**：QLoRA = 把冻结主干 4-bit NF4 量化存储 + 微调时反量化计算 + 只训 LoRA 增量（bf16），配合双量化压缩量化常数、分页优化器防显存尖峰；NF4 让量化误差对正态分布权重最小，双量化把每 64 权重一块的量化常数再量化一次省下约 0.4 bit/参数量级。

**1. NF4（4-bit NormalFloat）。** 分位数量化：预训练权重近似零均值正态，把正态分布的分位点作为码本，每个 bin 内点数相等，量化误差期望最小；相比均匀 int4 在同样 4 bit 下显著降低量化误差。存储 4 bit，计算时按需反量化到 bf16，前向反向都在反量化后的高精度值上进行，LoRA 梯度不受量化噪声直接影响。

**2. 双量化（double quantization）。** 分块量化引入量化常数（absmax），每 64 个权重存一个 fp32 常数，约占 0.5 bit/参数；对这批常数再做一次 8-bit 量化并把块间均值减掉，摊薄到约 0.127 bit/参数，65B 上省 GB 级显存。

**3. 其余两件套与效果边界。** 分页优化器：优化器状态显存不足时换页到 CPU/NVMe，防止长序列 batch 的显存尖峰 OOM。QLoRA 的结论是 4-bit 主干 + LoRA 能逼近 16-bit 全参微调的质量，让大模型微调平民化；但要注意它省的是「冻结权重的存储与激活读带宽」，优化器状态只针对 LoRA 参数，真正训全参时不能直接套用，且对量化超敏感的任务（极小数据）可能有轻微损失。''',
        "keyPoints": [
            "NF4：正态分位码本，4-bit 下量化误差最小",
            "双量化：量化常数再量化，约省 0.37 bit/参数",
            "计算时反量化回 bf16，只训 bf16 LoRA 参数",
            "分页优化器防显存尖峰；主干存储省但优化器只管 LoRA",
        ],
        "followUps": [
            {"q": "QLoRA 训练为什么不能把主干也省掉计算量？", "a": "前向反向仍要在 16-bit 反量化后的权重上做矩阵乘，省的是显存存储而不是计算量；要省算力得用低比特计算内核或更激进的量化感知训练，这与 QLoRA 的「存储量化、计算高精度」设计是两回事。"},
        ],
    },
    {
        "id": "posttrain-013",
        "topic": "PEFT",
        "type": "八股",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["腾讯", "百度", "面壁智能"],
        "years": ["2023", "2024"],
        "question": "对比 LoRA 和 prompt tuning / prefix tuning / p-tuning 这类软提示方法，各自的长短板？",
        "answerMd": r'''**一句话核心**：软提示方法只在输入或激活层注入少量可训练连续向量（<0.1% 参数），完全不动权重，容量小、对任务行为的改变浅；LoRA 改写权重增量，容量大、与模型深度耦合；模型越大软提示相对越有竞争力，但当前工程主流是 LoRA 系。

**1. prompt tuning。** 只在 embedding 层前拼 k 个可训练虚拟 token，参数量为 $k \times d$；实现最简单，但容量最小，小模型上明显落后微调，有「规模才是解药」的说法（模型越大差距越小）。

**2. prefix tuning / p-tuning v2。** 把可训练前缀放进每一层的 KV（重参数化经 MLP 生成），相当于每层都有任务特定的「记忆」，容量比 prompt tuning 大；问题是在注意力里持续占据上下文长度，压缩有效窗口，且多任务时 prefix 切换管理复杂。

**3. 对比 LoRA。** LoRA 作用于全部线性层、随前向逐层生效，不占上下文长度、推理可离线合并为零开销；表达力显著更强，风格到知识都能适配。软提示的优势在于极致参数效率、一个 batch 可同时跑几十个任务的 prompt（免切换权重）、完全隔离不污染底座。选型：任务极多且每个任务很轻 → 软提示；任务少但深 → LoRA；生产里多数团队收敛到 LoRA/全参两档。''',
        "keyPoints": [
            "prompt tuning：embedding 层虚拟 token，参数最少容量最小",
            "prefix/p-tuning v2：逐层 KV 前缀，容量大些但占上下文",
            "LoRA 改权重增量，不占窗口、可合并零开销",
            "软提示适合海量轻任务多路复用；主流生产是 LoRA",
        ],
        "followUps": [
            {"q": "为什么软提示方法随模型规模增大差距缩小？", "a": "大模型表征冗余度高，任务适配所需的「方向」更容易被少量连续向量在激活空间里定位；这与 LoRA 低秩有效是同一现象的两面——底座越强，后训练所需的本征维度越低。"},
        ],
    },
    {
        "id": "posttrain-014",
        "topic": "PEFT",
        "type": "八股",
        "difficulty": 3,
        "frequency": 4,
        "companies": ["字节", "阿里", "NVIDIA"],
        "years": ["2024", "2025"],
        "question": "LoRA 训练完怎么部署？什么场景要合并权重，什么场景要保留多 adapter？",
        "answerMd": r'''**一句话核心**：单任务长期服务就把 $\Delta W = \frac{\alpha}{r}BA$ 合并进 $W$ 用普通推理引擎跑零开销；多业务/多租户/AB 实验则保留独立 adapter 在同一底座上热切换，用 S-LoRA/Punica 这类多 adapter 服务框架共享主干 KV 与显存。

**1. 合并部署。** 合并是纯线性代数：$W \leftarrow W + \frac{\alpha}{r}BA$，浮点误差可忽略；合并后与普通模型无差别，vLLM/TensorRT-LLM 全速运行。注意：量化主干上合并前要先确认目标精度（在反量化权重上合并再按需量化，避免两次误差叠加）；合并是不可回滚操作，保留 adapter 原件以便撤销。

**2. 多 adapter 服务。** 场景：一个底座挂几十个业务 adapter、灰度对比不同 adapter、个性化微调按用户加载。瓶颈在切换开销与显存碎片，方案是共享底座权重 + 每个 adapter 只驻留 A/B 小矩阵，动态换入换出（S-LoRA 的 unified paging、Punica 的 kernel 融合），把千级 adapter 服务成可能；代价是 kernel 路径比合并版略慢。

**3. 实践建议。** 90% 场景合并就够：简单、快、无额外依赖；出现「同底座多任务并存、频繁发布回滚」时再上多 adapter 框架。混合策略也常见——主力任务合并，长尾任务 adapter 化。另外合并前务必用同一批评测回归，确认合并版与未合并版数值一致（bf16 精度下可能有微小偏差）。''',
        "keyPoints": [
            r"合并：$W + (\alpha/r)BA$，零推理开销，适合单任务长期服务",
            "量化模型先反量化合并再量化，防误差叠加，保留原件可回滚",
            "多 adapter：共享底座 + A/B 矩阵热切换（S-LoRA/Punica）",
            "按业务形态选择，可主力合并 + 长尾 adapter 混合",
        ],
        "followUps": [
            {"q": "多个 LoRA 能合并成一个吗？", "a": "线性叠加时可以：各 adapter 的增量按权重系数相加后一次合并；但如果它们来自不同秩/不同模块配置或训练目标冲突，直接合并会互相干扰，效果需实测，通常做法是先各自合并为全量差值再做任务算术式加权。"},
        ],
    },
    {
        "id": "posttrain-015",
        "topic": "PEFT",
        "type": "八股",
        "difficulty": 4,
        "frequency": 3,
        "companies": ["NVIDIA", "智谱", "微软"],
        "years": ["2024", "2025"],
        "question": "rsLoRA 和 DoRA 分别对 LoRA 做了什么改进？解决了什么问题？",
        "answerMd": r'''**一句话核心**：rsLoRA 把缩放从 $\alpha/r$ 改成 $\alpha/\sqrt{r}$，修正大秩时更新被过度缩小、训练不稳定的问题；DoRA 把权重分解为幅度与方向两个分量，对方向分量施加 LoRA，使更新更接近全参微调的「幅度稳、方向变」模式。

**1. rsLoRA。** 原始缩放 $\alpha/r$ 下，$BA$ 的谱范数随 r 增长而缩放项随 r 衰减，大秩时增量信号被压得过小，等效学习率不当、训练不稳；改为 $\alpha/\sqrt{r}$ 使不同秩下增量量级可比（类比注意力里的 $1/\sqrt{d}$），在高秩设置下更稳、效果更好，小秩时与原版接近。

**2. DoRA。** 把 $W$ 分解为幅度 $m = \|W\|_{col}$ 与方向 $V = W/\|W\|_{col}$：微调时冻结或低频更新幅度，用 LoRA 更新方向，再把两分量重组。观察依据是分析发现全参微调中幅度与方向的变化呈负相关、而 LoRA 只调一个分量做不到；DoRA 学到的更新模式更接近全参，小数据与低秩下增益更明显，代价是每次前向多做归一化与幅度合并，比 LoRA 略贵。

**3. 怎么看待这类改进。** 它们与 LoRA+（AB 学习率分离）、PiSSA（用主成分初始化 A/B）同属「把 LoRA 的初始化/缩放/梯度流修正到更接近全参微调」的谱系；单点收益通常 1 个点以内，选型时优先保证「全线性层覆盖 + 合适秩」，再考虑这些变体。''',
        "keyPoints": [
            r"rsLoRA：$\alpha/\sqrt{r}$ 缩放，修大秩训练不稳",
            "DoRA：幅度-方向分解，方向上做 LoRA",
            "两者都在缩小与全参微调的更新模式差距",
            "单点收益有限，先保证覆盖与秩再上变体",
        ],
        "followUps": [
            {"q": "DoRA 与全参微调还有差距的根源在哪？", "a": "低秩约束本身限制了方向子空间的维度，且幅度更新被弱化；对于需要注入大量新知识的任务，结构改进补不上容量差距，还是要靠升秩、全覆盖或直接全参。"},
        ],
    },
    {
        "id": "posttrain-016",
        "topic": "PEFT",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["字节", "快手"],
        "years": ["2024", "2025"],
        "question": "手写一个 LoRA 线性层，要求支持前向计算与权重合并。",
        "answerMd": r'''**一句话核心**：实现冻结原 Linear、旁路 $A/B$ 低秩矩阵的前向 $Wx + \frac{\alpha}{r}B(Ax)$，A 高斯初始化、B 置零保证起点等价，merge 时 $W \leftarrow W + \frac{\alpha}{r}BA$。

**易错点。** 一是忘记把 base 参数 requires_grad 关掉，导致优化器状态爆显存；二是 B 未零初始化（训练起点不等价原模型）；三是 dtype：量化主干场景下 base 是 4-bit 包装层，合并要先反量化；四是 alpha 缩放别丢。

**维度与参数账。** 以 $d_{in}=d_{out}=4096$、$r=16$ 为例，原矩阵约 16.8M 参数，LoRA 侧 $(r \times d_{in}) + (d_{out} \times r) \approx 131K$，约 0.8%；挂满一层 Transformer 的全部线性层，可训练参数通常在总量的 1% 以内。面试时能讲清梯度只走 A/B 分支、base 分支只参与前向但梯度会穿过它传到输入侧（stop_gradient 语义不同于 detach 整个分支），即可覆盖绝大多数追问。合并时注意先 cast 到与 base 相同的 dtype 再相加，避免 bf16 精度损失。

**延伸与自检。** 生产版通常再加两点：支持 per-layer 的 r 与 alpha 配置（对注意力与 MLP 用不同秩）；提供 unmerge 能力（减回增量）便于切换 adapter 做多任务服务。写完自检三步：零初始化下 forward 输出与原 Linear 逐元素一致；merge 后再 forward 与合并前完全一致（浮点误差内）；只把 lora_a、lora_b 传给优化器时参数量符合预期。这三条对应了本题最常被追问的三个正确性陷阱。''',
        "keyPoints": [
            "前向：base(x) + (x@A^T@B^T) * alpha/r",
            "A 随机初始化、B 零初始化，起点等价原模型",
            "冻结 base 参数，优化器只收 A/B",
            "merge：W += (alpha/r) * B @ A，注意 dtype 与量化",
        ],
        "followUps": [
            {"q": "为什么训练时通常不合并、推理时才合并？", "a": "训练中 A/B 每步在变，频繁改写 W 会破坏优化器对权重的状态一致性并引入同步开销；旁路结构还便于多 adapter 并存与回滚。推理阶段参数固定，合并可消除两条矩阵乘的额外延迟。"},
        ],
        "code": {
            "lang": "python",
            "caption": "LoRA 线性层与合并",
            "content": '''import torch
import torch.nn as nn

class LoRALinear(nn.Module):
    def __init__(self, base: nn.Linear, r: int = 8, alpha: int = 16,
                 dropout: float = 0.05):
        super().__init__()
        self.base = base
        for p in self.base.parameters():     # 冻结主干
            p.requires_grad_(False)
        self.scaling = alpha / r
        self.lora_a = nn.Parameter(torch.empty(r, base.in_features))
        nn.init.kaiming_uniform_(self.lora_a, a=5 ** 0.5)
        self.lora_b = nn.Parameter(torch.zeros(base.out_features, r))  # B 置零
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        out = self.base(x)
        delta = (self.dropout(x) @ self.lora_a.T) @ self.lora_b.T
        return out + delta * self.scaling

    @torch.no_grad()
    def merge(self):
        # W <- W + (alpha/r) * B @ A，之后可按普通 Linear 部署
        self.base.weight.data += self.scaling * (self.lora_b @ self.lora_a)'''
        },
    },
    # ---------------------------------------------------------------- RLHF 全流程
    {
        "id": "posttrain-017",
        "topic": "RLHF",
        "type": "八股",
        "difficulty": 3,
        "frequency": 5,
        "companies": ["字节", "阿里", "智谱", "DeepSeek"],
        "years": ["2023", "2024", "2025"],
        "question": "画出 RLHF 的完整三阶段流程，每个阶段的输入输出和关键设计点是什么？",
        "answerMd": r'''**一句话核心**：RLHF 三阶段 = 预训练模型 → 监督微调（SFT 得到对齐起点 π_SFT）→ 奖励模型训练（人类偏好成对数据 + Bradley-Terry 损失）→ PPO 强化学习（最大化 RM 打分并受 KL 约束不偏离 SFT）；每阶段的输出都是下一阶段的依赖，质量逐级传导。

**1. SFT 阶段。** 输入是高质量演示数据（人写的或强模型蒸馏），输出行为合格的 π_SFT；设计点：格式与模板统一、风格与安全基线建立。它是后续 RL 的参考策略（π_ref）与探索起点，质量差会让 RM 训练和 PPO 全程漂移。

**2. 奖励模型阶段。** 标注员对同一 prompt 的多个回答做排序（成对/列表），训练 RM 对 $(x, y)$ 输出标量分；损失用 BT 成对比较。设计点：标注规范（什么算更好：正确性优先于流畅性）、难度分层、一致性检验（同一题重复标、多人标注一致性）、长度等无关变量控制。RM 质量上限直接决定 RL 上限。

**3. PPO 阶段。** 策略是 π_SFT 初始化的 actor，优化 $\mathbb{E}[r_\phi(x,y)] - \beta \, \mathrm{KL}(\pi_\theta \| \pi_{\mathrm{SFT}})$；在线采样、RM 打分、advantage 估计、clip 更新。设计点：KL 系数防 reward hacking、prompt 分布多样、防长度/格式 exploit、实时监控 RM 分数与真实质量的偏离。训练完成后常再做一轮轻量 SFT（或混数据）修复可读性。''',
        "keyPoints": [
            "三阶段：SFT → 奖励模型 → PPO，环环依赖",
            "π_SFT 既是起点也是 KL 参考策略",
            "RM 决定上限：标注规范、一致性、难度分层",
            "PPO 靠 KL 约束与监控防 reward hacking",
        ],
        "followUps": [
            {"q": "能不能跳过 SFT 直接从基座做 RLHF？", "a": "很难。基座输出格式不稳定、无法采样出可供比较的高质量回答，RM 训练与 PPO 都会失效；至少需要轻量 SFT 建立行为格式，这也解释了 R1-Zero 这类纯 RL 工作要用规则奖励替代 RM 的原因。"},
        ],
    },
    {
        "id": "posttrain-018",
        "topic": "RLHF",
        "type": "八股",
        "difficulty": 4,
        "frequency": 4,
        "companies": ["字节", "阿里", "腾讯", "MiniMax"],
        "years": ["2023", "2024", "2025"],
        "question": "奖励模型的 Bradley-Terry 损失是怎么来的？成对数据训练 RM 的细节有哪些？",
        "answerMd": r'''**一句话核心**：BT 模型假设偏好概率由分差经 sigmoid 生成 $p(y_w \succ y_l|x) = \sigma(r(x,y_w) - r(x,y_l))$，对人类标注做极大似然得到损失 $\mathcal{L} = -\mathbb{E}[\log \sigma(\Delta r)]$；工程细节核心是「同 prompt 组内比较、多头打分、防长度与位置捷径」。

**1. 损失推导。** BT 模型把每个候选的优劣编码为标量实力分，比较胜率只依赖分差：$P(y_w \succ y_l) = \frac{e^{r_w}}{e^{r_w}+e^{r_l}} = \sigma(r_w - r_l)$。标注给出偏好后做 MLE 即负对数似然 $\mathcal{L} = -\log \sigma(r_w - r_l)$。梯度形式 $-(1-\sigma(\Delta))(\nabla r_w - \nabla r_l)$：分差越大梯度越小，天然聚焦难样本。RM 结构通常是基座 + 标量头（或最后一 token 的值）。

**2. 数据与训练细节。** 同一 prompt 采样多条回答构组，组内标注排序；实现上 batch 内 chosen/rejected 成对算分差。列表标注可拆成所有成对组合（加权）或用 Plackett-Luce 列表模型。标注质量：多人一致性过滤、重复题一致性检验、难度分层。归一化：BT 平移不变，单独一个 RM 的绝对分没有意义，比较只在其自身尺度内成立——跨 RM 分数不可直接比较。

**3. 防捷径。** 位置偏差（把选择位置打乱）、长度偏差（分差与长度相关性要监控）、风格偏差（控制措辞来源平衡）。RM 要配校准评估：分差与人工胜率的可靠区间（reliability diagram），而不只看成对准确率。''',
        "keyPoints": [
            r"$p = \sigma(r_w - r_l)$，MLE 得 $-\log\sigma$ 损失",
            "梯度聚焦分差小的难样本",
            "列表标注拆成对或用 Plackett-Luce",
            "BT 平移不变：RM 绝对分无意义、跨模型不可比",
            "防位置/长度/风格捷径，监控校准而非只看准确率",
        ],
        "followUps": [
            {"q": "RM 的成对准确率 90% 够用吗？", "a": "不一定。准确率是对被平均的，要看错误集中在哪：如果错在头部样本（高质量回答间比较）或系统性偏差（长度、格式），PPO 会放大这些错误；除了准确率还应看分差校准与在 RL 中的实际反馈效果。"},
        ],
    },
    {
        "id": "posttrain-019",
        "topic": "RLHF",
        "type": "八股",
        "difficulty": 4,
        "frequency": 3,
        "companies": ["MiniMax", "字节", "智谱"],
        "years": ["2024", "2025"],
        "question": "奖励模型会过拟合和被长度偏置，体现在哪？训练和使用时怎么缓解？",
        "answerMd": r'''**一句话核心**：RM 在训练分布内对齐标注但泛化差，策略一外推分数就失真；长度偏置表现为分数与回答长度正相关，让 PPO 学会「堆长度」。缓解靠数据平衡、正则与集成、使用时的 KL 约束与分数监控，根本解是把 RM 当「会过期的探测器」持续迭代。

**1. 过拟合的表现。** 训练集成对准确率很高，但策略生成的新分布上分数与人类偏好脱钩；常见机制是 RM 学到了标注捷径（长 = 好、礼貌开头 = 好、列点 = 好），策略立刻利用这些特征把分数推高而质量不升。判断方法：用策略新采样数据做人工盲评与 RM 分数的相关性检验，随训练步数看相关性是否衰减。

**2. 缓解手段。** 数据层：长度分层标注、同长度对比较样本加权、覆盖策略外推区域（用当前策略采样的新数据持续回流标注，即迭代 RM）；模型层：RM 集成取均值或惩罚分歧（不确定的样本分数收缩）、对表征加正则、用大基座训 RM 提升泛化；使用层：KL 约束限制策略跑飞、分数上做长度归一或去偏变换、设置分数 clip。

**3. 长度偏置专项。** 训练时显式加入「长度差与偏好无关」的控制组（同质回答仅长度不同、偏好由内容决定）；也可以在损失里对长度特征做对抗去偏。但注意长度本身与质量弱相关是真实的，目标是去掉「纯因长而胜」的部分而非惩罚长回答。''',
        "keyPoints": [
            "过拟合 = 分布外分数失真，靠新数据回流检测",
            "长度偏置：分数与长度正相关被策略利用",
            "数据平衡 + RM 集成/分歧惩罚 + 迭代训练",
            "使用时 KL 约束、分数去偏与 clip，RM 持续更新",
        ],
        "followUps": [
            {"q": "为什么 RM 集成比单模型更能防 hack？", "a": "单模型的决策边界外有大量未标注区域，策略可以找到高分洞；集成成员的误差方向不同，在洞上的分数分歧大，取均值会平滑掉虚假高峰，惩罚分歧则直接压低不确定区域的可利用性。"},
        ],
    },
    {
        "id": "posttrain-020",
        "topic": "RLHF",
        "type": "八股",
        "difficulty": 4,
        "frequency": 5,
        "companies": ["DeepSeek", "字节", "月之暗面", "Anthropic"],
        "years": ["2023", "2024", "2025"],
        "question": "RLHF 里的 KL 约束是干什么的？惩罚项加在哪里？系数怎么调？",
        "answerMd": r'''**一句话核心**：KL 项把策略钉在参考策略（SFT 模型）附近，防止策略钻 RM 空子、语言分布崩坏和灾难性遗忘；实现上既可作为目标里的显式正则，更常被折进每 token 的 shaped reward：$r_t = r^{RM} \cdot \mathbb{1}[t=最后] - \beta \log \frac{\pi_\theta(a_t|s_t)}{\pi_{ref}(a_t|s_t)}$；β 小了 hack、大了不学习，常用 0.01~0.05 起步按监控调。

**1. 为什么需要。** RM 只在人类数据分布附近可信，策略有无限优化压力必然外推；无约束的 PPO 会找到 RM 的对抗样本（高分低质），还会出现语言混杂、乱码、通用能力崩塌。KL 约束等价于让优化目标变为「在 SFT 邻域内最优」，保证改进是平滑的。

**2. 加在哪里。** 两种等价视角：目标函数里加 $-\beta \mathbb{E}_{y\sim\pi_\theta} \mathrm{KL}(\pi_\theta \| \pi_{ref})$（对 $\pi_\theta$ 是非平稳项，PPO 更新时另一份梯度要小心）；主流实现是把 KL 按 token 折进 reward shaping，只影响 advantage 估计而不给策略额外梯度路径，估计常用 k3 无偏估计量 $\frac{\pi_{ref}}{\pi_\theta} - \log\frac{\pi_{ref}}{\pi_\theta} - 1$。注意 ref 模型通常是冻结的 SFT，也有工作把 ref 动态更新为 EMA 策略。

**3. 调参经验。** β 过大：RM 分数几乎不动、模型学不到东西，表现为 RM reward 曲线平坦；过小：reward 快速上升但人工评测变差、长度爆炸、语言崩坏——这是最危险的静默失败。监控三件套：KL 随步数曲线（应在 5~30 nats 级别的量级内稳定）、RM 分数与人工盲评的相关性、长度分布漂移。自适应方案（按当前 KL 动态调 β）也常被使用。''',
        "keyPoints": [
            "作用：防 reward hacking、防语言崩坏、防遗忘",
            "实现：目标正则 or token 级 shaped reward（主流）",
            "估计用 k3：ref/θ - log(ref/θ) - 1，无偏且非负",
            "β 小则 hack 大则不学，监控 KL 曲线与盲评相关性",
        ],
        "followUps": [
            {"q": "KL 惩罚放进 reward 和放进 loss 有什么区别？", "a": "放 reward 只影响 advantage 与探索方向，策略梯度路径更干净、PPO 目标保持单项；放 loss 则 KL 有自己的梯度项（需要另一份前向），等价但实现上容易与 clip 交互出 bug。理论最优解相同，工程上 reward shaping 更主流。"},
        ],
    },
    {
        "id": "posttrain-021",
        "topic": "RLHF",
        "type": "八股",
        "difficulty": 5,
        "frequency": 5,
        "companies": ["字节", "DeepSeek", "月之暗面", "阿里"],
        "years": ["2023", "2024", "2025"],
        "question": "RLHF 里的 PPO 具体怎么实现？有哪些模型在显存里，超参上有什么经验？",
        "answerMd": r'''**一句话核心**：RLHF-PPO 同卡池里同时活着四个模型——actor（策略，训练）、reference（SFT 冻结，算 KL）、reward model（打分）、critic（价值函数，训练），流程是 rollout 生成 → RM 打分 + KL shaping → GAE 算 advantage → clip 目标更新 actor 与 value 损失更新 critic；超参上 LR 1e-6 量级、KL β 0.01~0.05、clip 0.2、按 token 计 loss，对超参极其敏感。

**1. 显存与角色。** actor 与 critic 训练态（参数+梯度+优化器），reference 与 RM 推理态；7B  actor 全参 + 各 7B 伴生模型在百卡级上才舒服，因此工程上大量使用 LoRA-actor、RM 与 actor 共享底座、offload ref 等技巧。rollout 生成占训练时长的大头，用 vLLM 等推理引擎 + 权重同步做加速是标配。

**2. 一个迭代的计算流。** batch prompts → actor 采样回答（温度 0.7~1.0 保探索）→ RM 对整条回答打一个标量（常放最后 token）→ 逐 token 算 KL shaping 得 shaped reward → critic 对每个 token 估 $V(s_t)$ → GAE 得 $\hat A_t$ → PPO clip 更新若干 epoch（一般 1~4）→ 同步 reference 所需权重（不变）→ 下一批。监控：KL、RM 分、长度、熵、response 各项指标。

**3. 超参经验。** 策略 LR 1e-6~5e-6（比 SFT 再小），critic LR 稍大；全局 batch 数十~数百 prompt，每 prompt 1~4 条回答；KL β 0.01~0.05；advantage 白化；value clip 与 policy clip 类似；熵正则防早熟；生成温度与 top-p 影响探索-稳定性。常见翻车点：KL 估计错符号、critic 从随机初始化导致早期 advantage 噪声大（用 RM 或 SFT 分数初始化 critic 更稳）、RLHF 中 PPO 对 batch 内 prompt 难度分布敏感。此外 rollout 常用 vLLM 独立部署，权重同步频率与训练吞吐直接相关，完全异步化会引入 off-policy 偏差，需要在这两者间显式权衡。''',
        "keyPoints": [
            "四模型：actor/critic 训练态 + reference/RM 推理态",
            "流程：rollout → RM 打分 → KL shaping → GAE → clip 更新",
            "LR 1e-6 量级、β 0.01~0.05、clip 0.2、advantage 白化",
            "rollout 是瓶颈：推理引擎 + 权重同步是标配",
            "critic 初始化要重视，熵正则防早熟",
        ],
        "followUps": [
            {"q": "为什么 RLHF 的 PPO 需要的样本量远大于 SFT？", "a": "RL 是在线探索：每条回答只提供一次带噪声的标量反馈，信号密度远低于 SFT 的 token 级监督；加上 advantage 估计方差大、可信更新占比低，需要海量 rollout。这也是 GRPO/拒绝采样等「榨干每条 rollout 信息」方法的动机。"},
        ],
    },
    {
        "id": "posttrain-022",
        "topic": "RLHF",
        "type": "八股",
        "difficulty": 4,
        "frequency": 4,
        "companies": ["字节", "腾讯", "Anthropic", "MiniMax"],
        "years": ["2023", "2024", "2025"],
        "question": "举几个真实的 reward hacking 案例，系统性防御手段有哪些？",
        "answerMd": r'''**一句话核心**：reward hacking 是策略把 RM/规则的漏洞当作优化目标：典型如堆长度与格式套模板、复读关键词、代码绕过测试、安全模型「拒答一切」、讨好性话术；防御是一个体系——KL 约束、奖励设计硬化、RM 迭代与集成、规则校验兜底、上线监控。

**1. 典型案例。** 长度 exploit：回答越长分越高 → 冗长注水；格式 exploit：多列点、加粗标题、礼貌开场白 → 模板化空洞内容；复读 exploit：重复问题或关键词提高某些 RM 特征；代码：生成大量浅测试或改断言让测试通过、硬编码输出；数学：只输出答案跳过程序（若 RM 偏好简洁）；安全 RM：学会对一切敏感话题拒答拿「安全分」，可用性崩塌；sycophancy：附和用户观点拿好感分；多轮场景把功劳话术前置。

**2. 防御体系。** 第一层，奖励设计：能用规则判定的（答案对错、格式、编译测试）就用规则硬奖励，别留给模型分；把「不可游戏」的部分显式编码（如长度惩罚、重复惩罚）。第二层，KL 约束与早停：限制偏离 SFT 的幅度，监控 RM 分与真实指标背离即停。第三层，RM 质量：迭代式用策略新样本回流标注、集成与不确定性收缩、对抗样本加入训练。第四层，多目标制衡：helpfulness 与 harmlessness 分开建模或 rubric 加权，避免单目标被钻。第五层，评测兜底：固定盲评集人工评估，RM 涨分但盲评不涨就触发回滚。

**3. 认知。** Goodhart 定律在 LLM RL 里是常态而非意外，防御目标是「提高 hacking 的成本、缩短发现时间」，而不是幻想一次消除。''',
        "keyPoints": [
            "案例：长度/格式/复读、代码绕测试、安全全拒答、讨好",
            "规则能判定的用硬奖励，减少可游戏空间",
            "KL 约束 + RM 回流迭代 + 集成不确定性收缩",
            "多目标制衡，盲评集兜底，背离即回滚",
        ],
        "followUps": [
            {"q": "规则奖励会不会被 hack？", "a": "会，只是更容易发现：答案是单选时模型可能输出裸选项骗过校验器，代码可用单测特判绕过；规则奖励要与任务语义强绑定并随机化校验细节，同时保留格式约束防止裸答案这类退化行为。"},
        ],
    },
    {
        "id": "posttrain-023",
        "topic": "RLHF",
        "type": "手撕",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["字节", "百度"],
        "years": ["2024", "2025"],
        "question": "手写：奖励模型的 Bradley-Terry 成对损失，并带出成对准确率与梯度含义。",
        "answerMd": r'''**一句话核心**：chosen 与 rejected 各过 RM 得标量分，损失 $-\log\sigma(s_w - s_l)$；准确率看分差是否为正，梯度 $-(1-\sigma(\Delta))(\nabla s_w - \nabla s_l)$ 说明分差大时梯度自动变小。

**实现要点。** 用 F.logsigmoid 数值稳定；batch 内成对比较时确保 chosen/rejected 来自同一 prompt 组；监控指标除 loss 外要看成对准确率和分差分布，分差持续变小说明模型在难样本上收敛。变体：加 margin（$\sigma(\Delta - m)$）或列表排序损失（RankNet 风格）。

**数据组织。** 一个 prompt 常有 2~8 条候选、标注给出偏序：实现上拆成全部满足偏序的成对组合（加权防某题主导梯度），batch 维度上是 chosen/rejected 两条序列并行走同一次前向再取差。标量头池化位置要用最后一个非 pad token，padding 侧不能污染分数。训练 RM 还要定期评估校准：把验证集按分差分桶，看每桶实际人工胜率是否单调——分差大却胜率不过半说明尺度失真。

**结构补充。** 标量头通常是一个小 MLP 投影到 1 维，也有直接用输出层某 token 的未归一化 logit 当分数（省参数）；基座选择上 RM 常与策略同源但可以更大，更大的 RM 泛化更好但推理成本上升。训练时的正则可用轻量 dropout 与权重衰减，过拟合监控看训练/验证成对准确率的 gap。若做长度去偏，可在损失里加一组「仅长度不同、偏好固定」的控制对，或在分差里回归掉长度项。''',
        "keyPoints": [
            r"$-\log\sigma(s_w - s_l)$，logsigmoid 数值稳定",
            "同 prompt 组内成对，防跨题比较",
            "监控成对准确率与分差分布",
            "梯度随分差增大而衰减，聚焦难样本",
        ],
        "followUps": [
            {"q": "如果不加处理把不同 prompt 的回答组成对会怎样？", "a": "分差失去比较意义，RM 会转而学习 prompt 级别的分数偏置（如长 prompt 的回答整体压分/抬分），损坏组内排序能力；这也是为什么构造数据时要保证 pair 来自同一 prompt 的多个候选。"},
        ],
        "code": {
            "lang": "python",
            "caption": "Bradley-Terry 奖励模型损失",
            "content": '''import torch
import torch.nn.functional as F

def bt_rm_loss(chosen_scores, rejected_scores):
    """chosen_scores / rejected_scores: [batch] 同一 prompt 两条候选的 RM 分"""
    diff = chosen_scores - rejected_scores            # BT 分差 Δ
    loss = -F.logsigmoid(diff).mean()                 # -log σ(Δ)
    with torch.no_grad():
        acc = (diff > 0).float().mean()               # 成对准确率
        margin = diff.mean().item()                   # 平均分差监控
    return loss, acc, margin

# RM 打分通常取序列最后一个非 pad 位置的标量头输出：
def rm_score(score_head, hidden, last_idx):
    # hidden: [B, T, d]  last_idx: [B] 每条序列最后一个有效 token 位置
    pooled = hidden[torch.arange(hidden.size(0)), last_idx]
    return score_head(pooled).squeeze(-1)'''
        },
    },
    {
        "id": "posttrain-024",
        "topic": "RLHF",
        "type": "八股",
        "difficulty": 4,
        "frequency": 3,
        "companies": ["月之暗面", "智谱", "DeepSeek"],
        "years": ["2024", "2025"],
        "question": "为什么 RLHF 的 PPO 里 critic 这么难训？有什么缓解办法？",
        "answerMd": r'''**一句话核心**：LLM 的价值函数要在超高维状态（长 token 序列）上拟合一个分布极宽、目标不断移动的回归，且与策略同步变化导致自举不稳定；缓解靠好的初始化、GAE 降方差、值裁剪、小学习率、以及干脆不要 critic（GRPO/ReMax 路线）。

**1. 难在哪。** 一是回归目标非平稳：critic 拟合 $V^{\pi_{\theta}}$，而 π_θ 每步在变，相当于追逐移动靶；二是输入表示难度大：状态是「prompt + 部分生成文本」，价值可能主要取决于未来才写出的内容，长序列 credit assignment 天然难；三是稀疏奖励：整条回答只有一个 RM 分，token 级优势全靠自举传播，早期 critic 噪声直接污染 advantage；四是尺度问题：不同 prompt 的奖励范围差异大，value head 需要白化和裁剪防单个样本梯度爆炸。

**2. 工程缓解。** 初始化：用 RM 或 π_SFT 的价值头热启动；训练技巧：value loss clip、对 value 做 advantage 白化、critic 学习率大于 actor 但配强正则、逐步扩大 rollout 长度课程；估计层面 GAE 的 λ 调低可显著减方差（牺牲些偏差容忍）。更彻底的是放弃 critic：GRPO 用组内相对分数当优势（省掉价值网络但只能处理结果奖励可比的任务）、ReMax 用组均值 baseline，这解释了 2024 年后免 critic 方法在推理类任务上的流行。''',
        "keyPoints": [
            "非平稳目标 + 高维序列状态 + 稀疏结果奖励",
            "早期 critic 噪声污染 advantage，要热启动",
            "GAE、值裁剪、白化、课程化是标准稳定器",
            "免 critic 路线（GRPO/ReMax）是结构性回避",
        ],
        "followUps": [
            {"q": "critic 用 RM 初始化合理吗？两者函数形式差在哪？", "a": "合理且常见：RM 已学会评价整条回答的质量，作 value 初值能提供低噪声起点；但 RM 输出整条回答的期望回报，而 critic 需要 token 级条件价值，后续仍需训练校准位置相关部分。"},
        ],
    },
    # ---------------------------------------------------------------- 直接对齐
    {
        "id": "posttrain-025",
        "topic": "直接对齐",
        "type": "八股",
        "difficulty": 5,
        "frequency": 5,
        "companies": ["DeepSeek", "字节", "月之暗面", "Anthropic"],
        "years": ["2023", "2024", "2025"],
        "question": "完整推导 DPO：从 RLHF 目标推出闭式解，再得到隐式奖励和最终损失。",
        "answerMd": r'''**一句话核心**：DPO 从带 KL 约束的 RLHF 目标出发，先求出最优策略的闭式解 $\pi^*(y|x) \propto \pi_{ref}(y|x)\exp(r(x,y)/\beta)$，反解出奖励代入 Bradley-Terry 偏好模型，归一化项 $Z(x)$ 在分差中相消，得到只用策略与参考策略似然比表示的损失 $\mathcal{L}_{DPO} = -\mathbb{E}\log\sigma(\beta \Delta)$，从而绕开 RM 与 RL。

**1. 起点。** KL 正则的 RLHF 目标（对每个 prompt $x$）：
$\max_{\pi_\theta} \; \mathbb{E}_{y \sim \pi_\theta}[r(x, y)] - \beta \, \mathbb{D}_{KL}[\pi_\theta(y|x) \,\|\, \pi_{ref}(y|x)]$，其中 $\pi_{ref}$ 是冻结的 SFT 模型，$\beta > 0$。

**2. 闭式最优解。** 把目标展开成对 $y$ 的逐项形式，做变分推导（构造拉格朗日或直接配凑 softmax 形式）可得唯一最优：
$\pi^*(y|x) = \frac{1}{Z(x)} \, \pi_{ref}(y|x) \exp\left(\frac{1}{\beta} r(x, y)\right)$，配分函数 $Z(x) = \sum_y \pi_{ref}(y|x) \exp\left(\frac{r(x,y)}{\beta}\right)$ 只依赖 $x$。

**3. 反解奖励。** 对上式取对数整理：
$r(x, y) = \beta \log \frac{\pi^*(y|x)}{\pi_{ref}(y|x)} + \beta \log Z(x)$。奖励由「策略与参考策略的对数似然比」加一个与 $y$ 无关的项表达。

**4. 代入 BT 模型消掉 $Z$。** 偏好概率 $p(y_w \succ y_l|x) = \sigma(r(x,y_w) - r(x,y_l))$，两奖励相减时 $\beta \log Z(x)$ 相消，得到隐式奖励 $\hat r_\theta(x,y) = \beta \log \frac{\pi_\theta(y|x)}{\pi_{ref}(y|x)}$，于是可直接对偏好数据做极大似然：
$\mathcal{L}_{DPO}(\theta) = -\mathbb{E}_{(x, y_w, y_l)}\left[\log \sigma\left(\beta \log \frac{\pi_\theta(y_w|x)}{\pi_{ref}(y_w|x)} - \beta \log \frac{\pi_\theta(y_l|x)}{\pi_{ref}(y_l|x)}\right)\right]$

**5. 理解。** 它等价于在 BT 假设下做「策略空间里的 RL」，隐式奖励的梯度同时拉开 chosen 的相对似然、压低 rejected；$\beta$ 控制偏离强度（小 β 更激进）。从梯度看，$1-\sigma(\beta\Delta)$ 让已经分对的样本自动降权，训练自然聚焦难样本。$\log Z(x)$ 对任意词表都不可显式计算，但在分差中完美相消——这是 DPO 能绕开奖励模型与采样、直接做监督训练的关键。代价是优化只在离线数据分布上进行，见第 27 题的失效分析。''',
        "keyPoints": [
            r"闭式解 $\pi^* \propto \pi_{ref} \exp(r/\beta)$ 是整个推导的枢纽",
            r"反解 $r = \beta \log(\pi^*/\pi_{ref}) + \beta \log Z$",
            "BT 分差中 $Z(x)$ 相消，得隐式奖励",
            r"$\mathcal{L} = -\log\sigma(\beta \Delta_{logratio})$，直接监督训练",
            "DPO = 离线偏好数据上的极大似然，无需 RM 与采样",
        ],
        "followUps": [
            {"q": "β 取大取小分别意味着什么？", "a": "β 是 KL 惩罚强度：大 β 时隐式奖励尺度小，策略被拉住贴着参考策略，训练稳但改进慢；小 β 隐式奖励变尖锐，等效更强的优化压力，容易过优化 rejected、拉长输出并放大分布偏移。"},
        ],
    },
    {
        "id": "posttrain-026",
        "topic": "直接对齐",
        "type": "八股",
        "difficulty": 4,
        "frequency": 4,
        "companies": ["字节", "阿里", "DeepSeek"],
        "years": ["2023", "2024", "2025"],
        "question": "DPO 和 PPO 在机制上有哪些本质区别？分别适合什么场景？",
        "answerMd": r'''**一句话核心**：PPO 是在线 on-policy 的 RL：自己采样、RM 打分、策略迭代，能持续探索新分布但工程重、难调；DPO 是离线监督式：在固定偏好数据上做似然优化，简单稳定但受数据分布限制、无探索。两者理论基础相通（同一 KL 正则目标），差异在于「是否在线、是否有显式奖励信号、是否能探索」。

**1. 机制对比。** 数据流：PPO 的训练数据来自当前策略的 rollout，随策略演化（on-policy）；DPO 的 $(x, y_w, y_l)$ 固定离线，通常由早期模型或更强模型采样。信号：PPO 每条 rollout 得到标量奖励，可对任意新行为评估；DPO 只有成对比较，无法对没覆盖的行为打分。模型数量：PPO 要 actor+critic+ref+RM 四模型，DPO 只要 policy+ref 两模型，实现与算力轻一个量级。优化性质：DPO 的隐式奖励随 θ 变化，loss 可降到很低但未必对应真实偏好提升（过优化）；PPO 有 KL+clip 双闸门但超参敏感。

**2. 适用场景。** DPO：有高质量偏好数据、算力有限、要快速迭代风格与指令遵循；以及作为 PPO 前的廉价基线。PPO：需要在线探索与硬指标提升（数学、代码可验证任务）、有完善 RM 与基础设施、追求质量上限；在线数据回流能持续修正 RM 错误。

**3. 融合趋势。** 实践常串联：SFT → DPO 快速拉齐 → 在线 RL 冲上限；也有 online DPO / 迭代 DPO（每轮用当前策略采样重标偏好）弥补分布偏移，本质是往 PPO 方向补在线性。''',
        "keyPoints": [
            "PPO 在线探索 + RM 实时打分；DPO 离线固定数据",
            "PPO 四模型重工程，DPO 两模型轻实现",
            "DPO 无探索、分布受限，易静默过优化",
            "常见串联：DPO 快速基线 → 在线 RL 冲上限",
        ],
        "followUps": [
            {"q": "迭代式 DPO 能解决离线分布偏移吗？", "a": "能部分缓解：每轮用当前策略采样并标注新偏好，数据分布跟随策略演化；但每轮之间仍是离线优化，标注延迟与成本限制了迭代频率，且新数据量不足时依然过优化。彻底解决要回到真正的在线 RL。"},
        ],
    },
    {
        "id": "posttrain-027",
        "topic": "直接对齐",
        "type": "八股",
        "difficulty": 4,
        "frequency": 4,
        "companies": ["月之暗面", "智谱", "腾讯"],
        "years": ["2024", "2025"],
        "question": "DPO 有哪些已知的局限和失效场景？实践中怎么补救？",
        "answerMd": r'''**一句话核心**：DPO 的失效都源于「离线 + 隐式奖励」：分布外行为没有约束导致过优化、隐式奖励在长回答上系统性偏高引入长度偏置、chosen/rejected 都很差时模型仍被推向 chosen；补救靠 SFT 先行、控 β 与训练轮数、在线/迭代化、长度校正。

**1. 过优化与分布偏移。** 隐式奖励 $\hat r = \beta \log(\pi_\theta/\pi_{ref})$ 的最大化对「离数据分布越来越远的行为」无界；数据覆盖不足的指令上，策略可以一边降 loss 一边偏离人类偏好。表现为训练 loss 很低、评测变差。补救：SFT 强基线（DPO 论文即先 SFT）、小学习率与早停、监控实际评测而非 loss。

**2. 长度与风格偏置。** log 似然比对长序列求和不归一，长回答的隐式奖励天然更大，DPO 训练后输出变长是普遍现象（被 SimPO 等用长度归一显式针对）；拒绝样本中包含过长回答时会加剧。补救：长度归一（SimPO）、按长度分层配对、对生成后做长度约束的解码。

**3. 质量差的偏好对。** chosen 只是「不那么差」时，DPO 强行提升 chosen 的似然，会把模型往平庸分布拉，甚至损害其原有能力（对齐税）；rejected 比 chosen 长或风格差异大时学到的是风格分类器。补救：数据清洗（质量下限、同源采样保证「唯一差异是质量」）、加入 SFT/NLL 锚定项（如 RPO/DPO+正则）、用 $\pi_{ref}$ 上的相对阈值过滤低质量对。

**4. 探索缺失。** DPO 无法发现数据外的更优行为，对可验证任务上限有限——这正是 RLVR 类在线方法回归的核心理由。''',
        "keyPoints": [
            "离线无界过优化：loss 好看、真实评测变差",
            "似然比不归一 → 长度偏置，SimPO 针对此",
            "差偏好对拉平庸分布，需清洗与锚定正则",
            "无探索，可验证任务上限低，被在线 RL 补位",
        ],
        "followUps": [
            {"q": "为什么 DPO 训练后模型输出常变长？", "a": "隐式奖励是逐 token 对数似然比的累加，长序列正项累积更多；同时 rejected 若平均更长，梯度会系统性压长序列、抬短序列的相对似然，两者叠加让策略偏向更长的 chosen 风格。"},
        ],
    },
    {
        "id": "posttrain-028",
        "topic": "直接对齐",
        "type": "八股",
        "difficulty": 4,
        "frequency": 4,
        "companies": ["字节", "MiniMax", "智谱"],
        "years": ["2024", "2025"],
        "question": "IPO、KTO、ORPO、SimPO 分别改了 DPO 的什么？一句话说清各自的动机。",
        "answerMd": r'''**一句话核心**：这条改进谱系都在修 DPO 的具体病灶：IPO 把 sigmoid 换成平方损失治过拟合，KTO 用前景理论处理非成对二元反馈，ORPO 把对齐折进 SFT 省掉参考模型，SimPO 用长度归一 + 目标 margin 治长度偏置、去掉参考模型。

**1. IPO（Identity Preference Optimization）。** 观察 DPO 在成对数据上可被无限推开似然比导致过拟合，把目标换成回归形式 $\mathbb{E}[(\hat h_\theta(y_w, y_l) - 1)^2]$（隐式奖励差回归到常数），约束更新幅度，小数据下更稳。

**2. KTO。** 现实反馈多是「这条回答好/坏」的二元标注而非成对；用行为经济学的 prospect theory（收益与损失的效用不对称）定义价值函数，只要求知道单条样本好坏即可训练，数据获取成本低，实验显示效果与 DPO 相当甚至更稳。

**3. ORPO。** 干脆不做两阶段：在 SFT 损失上加 odds-ratio 惩罚项，直接在偏好数据上联合训练「答案好 + 被偏好」，无需参考模型、无需先 SFT，训练流程最短；代价是与底座 SFT 强耦合，通用数据与偏好数据要混着喂。

**4. SimPO。** 把隐式奖励改成序列平均对数似然（长度归一）$\frac{\beta}{|y|}\log \frac{\pi_\theta(y|x)}{\pi_{ref}}$ 的无 ref 版本，加目标 margin γ 要求 chosen 超过 rejected 一个间隔；同时治长度偏置与参考模型开销，榜单表现强，但对实现细节（温度、margin）敏感。共同点：都是离线方法，天花板仍受数据分布约束，在线 RL 回潮后更多作为流水线中的轻量组件。''',
        "keyPoints": [
            "IPO：平方回归目标，治过拟合",
            "KTO：二元反馈 + prospect theory，免成对数据",
            "ORPO：odds-ratio 并入 SFT，免参考模型免两阶段",
            "SimPO：长度归一 + margin，治长度偏置免 ref",
        ],
        "followUps": [
            {"q": "这些变体有共同的理论框架吗？", "a": "多数可归到「对 KL 正则奖励最大化的不同代理目标」：DPO/IPO 是对闭式解的不同似然形式，SimPO 是改隐式奖励函数形状，KTO 是换偏好效用模型；ORPO 略特殊，把 SFT 项本身当 KL 锚。理解这点后新变体大多能快速归位。"},
        ],
    },
    {
        "id": "posttrain-029",
        "topic": "直接对齐",
        "type": "手撕",
        "difficulty": 4,
        "frequency": 4,
        "companies": ["字节", "DeepSeek", "月之暗面"],
        "years": ["2024", "2025"],
        "question": "手写 DPO 的损失函数：给定策略与参考模型对 chosen/rejected 的序列对数似然，实现完整 loss。",
        "answerMd": r'''**一句话核心**：损失是 $-\log\sigma\left(\beta[(\log\pi_\theta(y_w) - \log\pi_{ref}(y_w)) - (\log\pi_\theta(y_l) - \log\pi_{ref}(y_l))]\right)$，实现的关键是先把「序列对数似然」沿 token 求和算对（mask 掉 padding），四个量一起进 loss。

**实现要点。** sequence_logp 用 gather 取目标 token 的 log softmax 值并按 attention mask 求和；logits 与 target 要错一位（预测下一个 token）；β 一般 0.1；监控项：隐式奖励差（判断 chosen 是否真被拉开）、accuracy（$\beta\Delta > 0$ 比例）、以及平均长度变化。数值稳定用 F.logsigmoid。

**工程组织。** 实现上把 chosen 与 rejected 拼成同一 batch 做两次前向（policy 一次、reference 一次），reference 全程 no_grad；prefetch 时 reference 的 logp 可以离线预计算缓存，训练循环里只剩一次策略前向，速度接近普通 SFT。显存敏感时 policy 用 LoRA 并对四份 logp 各自累加后再组 loss。注意两个退化信号：reward_margin 持续增长而评测不动，说明在过优化；margin 长期贴零说明 β 过大或数据太弱。

**变体与追问。** 若把末行换成 IPO 的平方形式 $(\beta\Delta - 1)^2$ 即得 IPO；加长度归一（logp 除以 token 数）即朝 SimPO 靠近；加 SFT 的 NLL 正则项（对 chosen 加 $-\lambda\log\pi_\theta(y_w)$）是常见的防遗忘锚定。面试常追问 reference 的处理：ref 必须与 SFT 初始完全同参且冻结，若误用当前策略当 ref，损失会退化为常数零；以及 batch 内 chosen/rejected 必须等长拼接对齐，padding 位置 mask 不能漏。评测上 DPO 后要固定跑一组通用基准加风格敏感度测试，因为这类静默退化不会反映在训练 loss 里。''',
        "keyPoints": [
            "先实现正确的序列 logp（错位 gather + mask 求和）",
            "loss = -logsigmoid(β * (Δ_θ - Δ_ref))",
            "监控隐式奖励差、成对准确率、长度漂移",
            "logsigmoid 保证数值稳定",
        ],
        "followUps": [
            {"q": "为什么算序列 logp 时 logits 要向左错一位？", "a": "logits[t] 是看到前 t 个 token 时对第 t+1 个 token 的预测分布，所以要与 target=input_ids[t+1] 对齐；不错位会把监督目标整体偏移一个 token，等价于让模型预测「当前 token」，DPO 的似然差全部错乱，训练直接失效。"},
        ],
        "code": {
            "lang": "python",
            "caption": "DPO 损失",
            "content": '''import torch
import torch.nn.functional as F

def sequence_logp(model, input_ids, attn_mask):
    """整条序列的对数似然之和: [batch]"""
    logits = model(input_ids=input_ids,
                   attention_mask=attn_mask).logits[:, :-1]
    logp = F.log_softmax(logits.float(), dim=-1)
    tgt = input_ids[:, 1:]
    token_logp = torch.gather(logp, 2, tgt.unsqueeze(-1)).squeeze(-1)
    mask = attn_mask[:, 1:].to(token_logp.dtype)
    return (token_logp * mask).sum(-1)

def dpo_loss(pi_w, pi_l, ref_w, ref_l, beta=0.1):
    """四个入参均为 sequence_logp 输出: [batch]"""
    logits = beta * ((pi_w - ref_w) - (pi_l - ref_l))  # 隐式奖励差 * β
    loss = -F.logsigmoid(logits).mean()
    with torch.no_grad():
        acc = (logits > 0).float().mean()
        reward_margin = logits.mean().item()
    return loss, acc, reward_margin

# batch 组织：chosen/rejected 拼成一个 batch 一次前向（policy 与 ref 各一次）
# pi_w, pi_l = split(sequence_logp(policy, ids, mask))
# ref_w, ref_l = split(sequence_logp(ref, ids, mask).detach())'''
        },
    },
    # ---------------------------------------------------------------- GRPO 与推理对齐
    {
        "id": "posttrain-030",
        "topic": "GRPO 与推理对齐",
        "type": "八股",
        "difficulty": 4,
        "frequency": 5,
        "companies": ["DeepSeek", "月之暗面", "字节", "智谱"],
        "years": ["2025", "2026"],
        "question": "讲讲 GRPO 的原理和公式，它怎么替代了传统 RLHF 里的 PPO？",
        "answerMd": r'''**一句话核心**：GRPO（Group Relative Policy Optimization，出自 DeepSeekMath）对每个 prompt 采一组 G 条回答，用组内奖励归一化 $\hat A_i = \frac{r_i - \mathrm{mean}(r)}{\mathrm{std}(r)}$ 当作所有 token 共享的优势，从而删掉 critic；目标仍是 PPO 式 clip，加上对 ref 策略的 KL，配合可验证奖励成为 R1 系推理模型的主力算法。

**1. 组相对优势。** 同一问题采样 $o_1, ..., o_G \sim \pi_{old}$，各自得分 $r_1, ..., r_G$（规则判对错或 RM），优势 $\hat A_{i,t} = \frac{r_i - \frac{1}{G}\sum_j r_j}{\sqrt{\frac{1}{G}\sum_j (r_j - \bar r)^2}}$，对第 i 条回答的所有 token 取同一值。直觉：蒙特卡洛式的 baseline——同一题里答对 vs 答错的相对好坏不需要价值网络来估计。

**2. 目标函数。** token 级：
$\mathcal{J} = \mathbb{E}\left[\frac{1}{G}\sum_{i=1}^{G} \frac{1}{|o_i|}\sum_{t=1}^{|o_i|}\left(\min\left(\rho_{i,t}\hat A_{i,t},\, \mathrm{clip}(\rho_{i,t}, 1-\epsilon, 1+\epsilon)\hat A_{i,t}\right) - \beta \, \hat{\mathbb{D}}_{KL}[\pi_\theta \| \pi_{ref}]\right)\right]$，其中重要性比率 $\rho_{i,t} = \frac{\pi_\theta(o_{i,t}|\,q, o_{i,<t})}{\pi_{old}(o_{i,t}|\,q, o_{i,<t})}$，KL 用 k3 无偏估计。

**3. 相比 RLHF-PPO 的替代逻辑。** 传统管线里 critic 服务于「单条 rollout 的奖励基线」，GRPO 用同题多条回答互相比较，天然给出低方差 baseline，critic 可删；奖励端用可验证规则（答案正确、格式、编译通过）替代 RM，进一步砍掉奖励模型。KL 项在原论文里逐 token 进 loss，一些实现改挂到 reward 上，二者等价但梯度路径不同。剩余组件只有 policy + ref，显存和工程复杂度大降，这正是它在推理 RL 时代普及的原因（局限见第 rl 域深入题）。另外注意实现里常见的两个自由度：优势除不除 std（Dr.GRPO 认为除 std 引入难度偏差）、loss 按 token 平均还是按序列平均（后者引入长度偏差），这些细节 2025 年起被系统研究并催生了 DAPO/Dr.GRPO 等修正版。''',
        "keyPoints": [
            "同题采 G 条，组内归一得分即优势，无需 critic",
            "目标保持 PPO clip + k3 KL 估计",
            "可验证规则奖励替代 RM，砍掉奖励模型",
            "组件只剩 policy+ref，工程显存双降",
        ],
        "followUps": [
            {"q": "组内全对或全错时优势是多少？这有什么问题？", "a": r"全对或全错时 $r_i - \bar r = 0$，优势全为 0，该组对策略更新零贡献——样本被浪费，且这类组往往出现在任务过易或过难时。DAPO 的动态采样就是过滤或重采这类组，把算力花在有梯度信号的题上。"},
        ],
    },
    {
        "id": "posttrain-031",
        "topic": "GRPO 与推理对齐",
        "type": "八股",
        "difficulty": 3,
        "frequency": 4,
        "companies": ["DeepSeek", "字节", "MiniMax"],
        "years": ["2025", "2026"],
        "question": "GRPO 相比 PPO 在显存和工程上的优势具体有多大？付出什么代价？",
        "answerMd": r'''**一句话核心**：GRPO 删掉 critic 和 RM，训练态模型从 4 个降到 2 个（policy 训练 + ref 推理），7B 模型少一份参数+梯度+优化器状态和一份推理常驻，粗算省 30%~50% 显存并大幅简化流水线；代价是每题要采 G 条回答（rollout 成本 ×G）、组方差为 0 的浪费、以及只能用于奖励可比较的场景。

**1. 显存账。** PPO-RLHF：actor（参数+梯度+Adam 状态 ≈ 16 字节/参数）+ critic（同样 16 字节/参数，且常与 actor 同尺寸）+ ref 与 RM 推理态（各 2 字节/参数）。GRPO 去掉 critic：省掉一整份训练态；若再用规则奖励连 RM 也省。以 7B 全参 bf16 粗算，critic 一份约省 100GB+ 优化器与梯度显存（ZeRO 切分下摊到多卡），再加 RM 约 14GB。工程上 rollout/训练/参考三段流水线的同步点也更少。

**2. 工程红利。** 无 critic 意味着没有 value 网络的训练稳定性问题、没有 value/policy 学习率配平；奖励规则化后调试从「模型黑盒」变成「可读的校验器」，badcase 可归因。这使得算法能在中等规模团队复现——R1 之后开源框架（verl 等）把 GRPO 做成默认选项。

**3. 代价。** rollout 数量乘 G（通常 4~16，长 CoT 下 token 成本显著）；组内无差异时零梯度（低效）；策略分布窄的题优势信号弱；对奖励必须「同题内可比」的要求排除了部分任务。后续工作（动态采样、off-policy 复用）大都在补这些短板。''',
        "keyPoints": [
            "删 critic（一份训练态）+ 规则奖励删 RM",
            "7B 量级粗省 30%~50% 训练显存与同步复杂度",
            "代价：rollout ×G、零梯度组、要求同题可比奖励",
            "无 value 稳定性问题，调试可归因到校验器",
        ],
        "followUps": [
            {"q": "G 怎么选？大了小了各有什么问题？", "a": "G 小（2~4）基线估计噪声大、优势不准；G 大基线稳但 rollout 成本线性涨，且难度低的题很快组内全对造成浪费。经验 8~16 起步，配合按题目难度动态调整采样数的课程化策略更省。"},
        ],
    },
    {
        "id": "posttrain-032",
        "topic": "GRPO 与推理对齐",
        "type": "场景",
        "difficulty": 4,
        "frequency": 3,
        "companies": ["智谱", "阶跃星辰", "DeepSeek"],
        "years": ["2025"],
        "question": "用 GRPO + 可验证奖励把一个 8B 基座训成数学解题模型，给出完整方案。",
        "answerMd": r'''**一句话核心**：管线 = 高质量数学 SFT 冷启动 → GRPO/RLVR 主训练（规则校验器给 0/1 奖励 + 格式约束）→ 分难度课程与动态采样 → 蒸馏或合并回通用能力；成败关键在冷启动质量、校验器严谨性和训练稳定性三板斧（clip、长度控制、采样过滤）。

**1. 冷启动。** 先用数十万条带简洁 CoT 的数学题做轻 SFT，保证：模型会用指定格式输出答案（如 \boxed{}）、正确率不为零（RL 需要可探索的成功样本）、回复可读。数据源：公开数学语料 + 强模型蒸馏轨迹，按难度分层标注（便于课程）。

**2. RLVR 主训练。** 奖励：答案与标准答案等价比对（符号化或数值容差）给 1，否则 0；加格式奖励（必须含规定标签与最终答案）；避免模型化奖励。GRPO 超参：G=8~16、clip 0.2、KL 系数小或 0（R1-Zero 式可不加 ref，看稳定性）、按 token 计 loss。题目课程：从正确率 20%~80% 的中等难度带起步（有信号），随训练上移难度；全对/全错的组动态过滤重采。

**3. 稳定性三板斧。** 长度控制：监控响应长度，超长软惩罚防 reward 由「碰运气长输出」主导；熵监控：熵塌缩前放宽 clip 上界或加熵正则；KL 与 SFT 数据回放防语言能力崩坏。

**4. 验收与收尾。** 评测用 held-out 数学集 + 过程可读性人工抽检 + 通用基准防遗忘；最后可把 RL 模型的新轨迹做拒绝采样再蒸馏回小模型，或与通用 chat 模型合并兼顾多能力。''',
        "keyPoints": [
            "冷启动保证格式、非零正确率与可读性",
            "0/1 规则奖励 + 格式奖励，避免模型化奖励",
            "难度课程 + 动态过滤全对全错组",
            "监控长度、熵、KL 三条曲线防崩",
            "验收含可读性与通用能力回归",
        ],
        "followUps": [
            {"q": "如果训练中正确率不动但长度猛涨，说明什么？", "a": "典型 reward hacking 前兆：模型发现长回答偶尔碰对或格式奖励可刷；应检查奖励是否被长度间接影响、收紧格式校验、引入长度惩罚或超长截断，并回滚到上一个检查点。"},
        ],
    },
    # ---------------------------------------------------------------- 蒸馏与迭代
    {
        "id": "posttrain-033",
        "topic": "蒸馏与迭代",
        "type": "八股",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["DeepSeek", "智谱", "百度"],
        "years": ["2024", "2025"],
        "question": "什么是拒绝采样微调（RFT）？它和 STaR、Best-of-N 蒸馏是什么关系？",
        "answerMd": r'''**一句话核心**：RFT = 用当前模型对每个问题采样多条回答，只保留答案正确的（可验证任务）再筛优，把这些「自己生成的正确轨迹」微调回去，形成采样-筛选-学习的自我迭代闭环；STaR 是同一思想的代表工作，Best-of-N + 蒸馏则是「采样在强者、学习在弱者」的跨模型版本。

**1. 机制。** 采样 N 条（温度 >0 保多样性）→ 校验正确性（标准答案比对、单测通过）→ 过滤与去重（按推理路径去重，避免同质样本）→ 加入 SFT 集再训练。它把「结果奖励」转成了「token 级监督」，比 RL 简单稳定，是 RL 前的高性价比杠杆：同样的算力下，正确路径直接当正样本，不需要 advantage 估计。

**2. 与 STaR 的关系。** STaR（Self-Taught Reasoner）提出 rationalization 变体：答错的题把标准答案作为提示让模型生成解释再学习，扩大困难题的覆盖；RFT 泛指这类拒绝采样数据自举，思想同源。

**3. 与 Best-of-N 蒸馏。** Best-of-N 是推理时扩展：采 N 条用验证器挑最好的输出；「Best-of-N 蒸馏」把这个被挑选的最优输出存下来训小模型或训回自身，等价于把搜索的收益固化成参数。区别在采样者与学习者是否同一个模型、以及是否有验证器介入。

**4. 局限。** 只能强化「已能做对」的模式，对做错的题无能为力（探索失败在采样里被丢掉）；自我迭代多轮后数据分布逐渐收窄，需要外部难题供给与多样性控制，否则收益饱和。''',
        "keyPoints": [
            "采样 → 验证正确 → 去重筛优 → 回灌 SFT，可迭代",
            "把结果奖励转成 token 级监督，比 RL 稳",
            "STaR 的 rationalization 补困难题覆盖",
            "局限：学不会做错的题，多轮后收益饱和",
        ],
        "followUps": [
            {"q": "拒绝采样数据要不要按推理路径去重？", "a": "要。同一题的多条正确回答常共享大段相同推理，不去重会让梯度集中在少数模式上，加剧过拟合与多样性塌缩；通常按最终答案 + 推理路径哈希/embedding 相似度控制每题保留的路径多样性。"},
        ],
    },
    {
        "id": "posttrain-034",
        "topic": "蒸馏与迭代",
        "type": "八股",
        "difficulty": 4,
        "frequency": 3,
        "companies": ["OpenAI", "DeepSeek", "智谱"],
        "years": ["2024", "2025"],
        "question": "过程奖励模型（PRM）和结果奖励模型（ORM）怎么选？Let's Verify Step by Step 说明了什么？",
        "answerMd": r'''**一句话核心**：ORM 只对最终答案打分（数据便宜、信号稀疏），PRM 对每个推理步骤打分（信号密集、可定位错误，但需要细粒度人工标注且易被 hack）；OpenAI 的 Let's Verify Step by Step 在数学推理上显示 PRM 的 best-of-N 与树搜索显著优于 ORM 与投票，确立了「过程监督优于结果监督」的结论——但代价与可扩展性（能否自动获得步骤标注）决定实际选型。

**1. 两者定义。** ORM：输入问题 + 完整解答，输出一个整体分；训练只需答案对错标签，可从自动校验大规模获得。PRM：对解答的每个步骤输出正确性分；训练需要步骤级标注（该论文人工标注了约 80 万步级别的数据），或用蒙特卡洛 rollout 估计每步价值来自动构造。

**2. 论文的核心发现。** 在 MATH 子集上，PRM 指导的 best-of-N 搜索优于 ORM 指导与多数投票，且随 N 增大优势扩大；「显著缓解了 ORM 的假阳性问题」——最终答案碰对但过程错误的解会被 PRM 压下去。同时论文指出 PRM 更难避免「教会模型只走被奖励认可的路径」的风险，且标注成本高。

**3. 选型逻辑。** 有可自动校验的中间步骤（代码单测、数学等价检查）→ 用规则做过程奖励，最便宜且难 hack；有预算做人工/模型步骤标注且任务错误代价高 → PRM；数据量大、只关心最终对错 → ORM + 大 N 采样。现代推理 RL 中过程奖励多用于数据筛选与课程，而非直接进 RL 目标，因为 RLVR 的 0/1 结果奖励更难被 hack。''',
        "keyPoints": [
            "ORM：答案级标签便宜、稀疏、假阳性多",
            "PRM：步骤级密集信号，需细标注或 MC 估计",
            "论文结论：PRM 搜索显著优于 ORM 与投票",
            "选型看步骤可自动校验性与标注预算",
            "RL 时代 0/1 结果奖励更抗 hack，PRM 多用于筛选",
        ],
        "followUps": [
            {"q": "PRM 怎么被 hack？", "a": "策略可以生成「看起来正确」的步骤骗过 PRM：冗长的平凡步骤刷分、把错误包装成合理试探；防御包括步骤采样与人工对照的持续更新、对步骤长度与模板化打惩罚、以及最终答案校验兜底。"},
        ],
    },
    {
        "id": "posttrain-035",
        "topic": "蒸馏与迭代",
        "type": "八股",
        "difficulty": 4,
        "frequency": 4,
        "companies": ["DeepSeek", "MiniMax", "面壁智能"],
        "years": ["2025", "2026"],
        "question": "黑盒蒸馏和白盒蒸馏的区别是什么？推理模型时代蒸馏小模型该怎么选？",
        "answerMd": r'''**一句话核心**：黑盒蒸馏只用教师输出的文本（SFT 式模仿轨迹），白盒蒸馏能用教师的 logits/隐状态（KD 损失对齐分布），信息量大但要求同词表与访问权；推理模型时代小模型的现实选择大多是「黑盒轨迹蒸馏 + 拒绝采样过滤」，配合可验证任务筛选，性价比高于自己跑 RL。

**1. 黑盒蒸馏。** 只需要 API：教师生成问题-解答对（可加轨迹），学生做 SFT。优点是简单、跨模型跨词表可行、数据可积累复用；缺点是只学到输出分布的「样本」，学不到分布本身的暗知识（教师对错误选项的概率）。R1 系列对 1.5B~70B 的蒸馏正是此路线：小模型数学代码能力大涨，说明强教师的长 CoT 数据里蕴含大量可模仿的推理模式。

**2. 白盒蒸馏。** 经典 KD：学生最小化与教师 softmax（带温度 T）的 KL，$L = T^2 \, \mathrm{KL}(p_T \| p_S)$；变体有对隐状态做 MSE、on-policy GKD（学生在自己采样上对齐教师分布，缓解 train-inference 错位）。优点是信号稠密、样本效率高；约束是要拿到 logits、同 tokenizer、推理成本高（教师在线前向），闭源模型不可能。

**3. 选型与组合。** 有教师权重且同词表 → 白盒（或混合：硬标签轨迹 + 软分布）；只有 API → 黑盒 + 数据工程（难度分层、拒绝采样、多样性控制）。注意蒸馏的两条边界：学生上限被教师输出分布框住（模仿不产生超越），蒸馏强风格可能带来安全对齐的退化（蒸馏数据的安全属性要单独管）。''',
        "keyPoints": [
            "黑盒：轨迹 SFT，跨词表可用，学不到暗知识",
            "白盒：KL(logits) 稠密信号，需同 tokenizer 与权重",
            "GKD 类 on-policy 蒸馏缓解分布错位",
            "蒸馏上限被教师框住，安全属性需单独处理",
        ],
        "followUps": [
            {"q": "蒸馏的学生和 RL 训练的学生比，长期差距在哪？", "a": "相同算力下蒸馏学生 pass@1 更高（模仿了成熟分布），但探索出的新解法少、pass@k 上限通常更低；RL 学生起点低、波动大，但能产生教师没有的行为。业届共识是两者互补：蒸馏打底、RL 精修。"},
        ],
    },
    {
        "id": "posttrain-036",
        "topic": "蒸馏与迭代",
        "type": "八股",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["腾讯", "百度", "面壁智能"],
        "years": ["2024", "2025"],
        "question": "模型自我迭代（用自己生成的数据训练自己）有哪些风险？怎么避免越训越差？",
        "answerMd": r'''**一句话核心**：自食其尾的风险是分布收缩与误差累积：合成数据长尾与模式被截断，多代之后多样性下降、幻觉自我强化、模型坍缩到高频模式；防护靠「外部锚点 + 质量门控 + 多样性保留」，纯自闭环的迭代几乎注定退化。

**1. 风险机理。** 采样丢尾巴：模型生成偏向高概率模式，低频知识逐渐缺席；误差自强化：错误内容被再次采样、再训练而获得似然，幻觉放大；模式坍缩：同质数据让输出多样性（熵）下降；评测漂移：用自己判自己，反馈回路失真。理论工作（模型坍缩）证明无新鲜数据的递归训练在极限下方差收缩。

**2. 防护原则。** 外部锚点：每轮混合足量真实人类数据或强外部模型数据，合成比例设上限；质量门控：可验证任务用规则判真伪，开放任务用强模型 + 人工抽检双通道，宁缺毋滥；多样性保留：按聚类分层采样、去重、覆盖长尾任务配额；误差隔离：训练前把「确认错误」样本剔除而不是降权，错误模式要有召回机制。

**3. 有效的自迭代形态。** 有外部奖励的闭环（拒绝采样 + 答案校验、RLVR）是安全的，因为错误无法伪装成正确；带新信息注入的（搜索、工具结果、专家校对）能持续增量；而「模型打分-模型生成-模型训练」的纯自闭环只能用于风格、格式类低风险适配。判断标准：错误能否被迭代外部的信号识破。''',
        "keyPoints": [
            "风险：分布收缩、误差自强化、多样性坍缩、评测自循环",
            "外部锚点混真实数据，合成比例设上限",
            "质量门控：可验证优先，开放任务强模型+人审",
            "纯自闭环只适合风格格式类低风险任务",
        ],
        "followUps": [
            {"q": "怎么量化监控模型是否在坍缩？", "a": "看三类曲线：输出多样性（n-gram/embedding 多样性、熵）、长尾评测子集的表现（小众任务、罕见知识）、生成数据与训练分布的覆盖率；若多样性单调下降且长尾持续恶化，即使主流评测持平也要警惕。"},
        ],
    },
    # ---------------------------------------------------------------- 评测与安全
    {
        "id": "posttrain-037",
        "topic": "评测与安全",
        "type": "八股",
        "difficulty": 3,
        "frequency": 4,
        "companies": ["字节", "阿里", "MiniMax"],
        "years": ["2024", "2025"],
        "question": "AlpacaEval、Chatbot Arena 这类对齐评测有什么局限？怎么避免被评测带偏？",
        "answerMd": r'''**一句话核心**：两者都是「偏好类」评测：AlpacaEval 用 LLM-judge 算胜率、Arena 用真人盲投算 Elo，共同问题是奖励了长度、格式、自信语气等风格因素而非真实能力，且可被针对性优化（judge 提示词已知、Arena 提交可刷）；防带偏要 style control、多源评测交叉与内部盲评集。

**1. AlpacaEval 系的坑。** judge 有系统偏好：更长、更多列表与加粗、礼貌开头更容易赢，导致模型为刷分而注水；官方后来加了 style control（对长度与格式做统计校正）但风格空间不止这两维；基准 prompt 集固定且公开，易过拟合。

**2. Arena 的坑。** 真人投票也有风格偏差（自信、emoji、语气），且投票者分布偏向特定人群与问题类型； Elo 对「提交频率与对抗调参」敏感；顶部模型差异常在噪声区间内。它测的是「讨喜度」多于「正确性」，对代码、数学这类可验证能力分辨率低。

**3. 健康的评测体系。** 分层：能力类（MMLU/GPQA/HumanEval/AIME 等有标准答案）为主，偏好类为辅；偏好类做 style control 与长度敏感性分析（同内容改长度看胜率变化）；内部保留不公开的盲评集与人工专家评估防过拟合；关注评测集污染检测。原则：把榜单当体检指标之一，不当优化目标——Goodhart 一旦发生，榜上提升反而是警告信号。''',
        "keyPoints": [
            "偏好评测奖励长度/格式/语气等风格因素",
            "AlpacaEval：judge 偏好 + 集公开，可被针对性优化",
            "Arena：投票人群偏差，测讨喜度多于正确性",
            "style control + 多源交叉 + 私有盲评集防带偏",
        ],
        "followUps": [
            {"q": "LLM-judge 评测怎么做偏置校正？", "a": "常见手段：位置随机化与交换一致性检验、长度差控制或回归校正、用 rubric 分项打分代替整体偏好、以人类标注为金标准校准 judge 的系统偏差；报告时同时给原始与校正结果更诚实。"},
        ],
    },
    {
        "id": "posttrain-038",
        "topic": "评测与安全",
        "type": "八股",
        "difficulty": 3,
        "frequency": 4,
        "companies": ["OpenAI", "字节", "智谱"],
        "years": ["2024", "2025"],
        "question": "GPQA、AIME、HumanEval 各自测什么？什么叫对齐税，怎么监控和减少？",
        "answerMd": r'''**一句话核心**：GPQA 测研究生级的科学推理（抗搜索）、AIME 测数学竞赛推理（可精确校验，推理模型主战场）、HumanEval 测代码生成（单测校验）；对齐税指对齐训练后模型在通用/基础能力上的下降，靠「双轨评测门禁 + 数据回放 + 对齐目标轻量化」控制。

**1. 三个基准的定位。** GPQA：专家设计的选择题，非专家靠搜索引擎也难做对，考真实学科推理，是「防数据污染的智力测试」；AIME：奥数题，答案唯一可校验，天然适配 RLVR 与测试时扩展，推理模型以此对标；HumanEval：函数补全 + 单测通过率，测基础代码合成，已被更难的 LiveCode/SWE-bench 系补充。三者分别覆盖科学、数学、代码三条可验证能力轴。

**2. 对齐税。** SFT/RLHF 收窄输出分布、强化特定格式与安全行为，会牺牲预训练的广度：表现为知识问答变差、生成多样性下降、复杂指令外能力退化（极端案例是安全模型拒答暴涨）。RLHF 阶段的 KL 约束本质就是在付「能力保持税」和「对齐收益」之间定价。

**3. 监控与减税。** 每轮后训练跑固定的通用回归套件（知识/推理/代码/多语言/长文本 + 安全与拒答校准），设发布门禁；数据层面混入预训练分布数据与通用指令；方法层面用轻量对齐（小 β、LoRA、DPO 短训）或合并策略（aligned 与 base 权重插值）找平衡点；最后区分「真下降」与「表达抑制」：同一模型放开格式约束重测，判断能力是否还在。''',
        "keyPoints": [
            "GPQA/AIME/HumanEval 覆盖科学/数学/代码可验证轴",
            "对齐税 = 对齐后通用能力与多样性的损失",
            "KL 约束是在收益与保持之间定价",
            "双轨评测门禁 + 数据回放 + 轻量对齐减税",
        ],
        "followUps": [
            {"q": "怎么区分能力真丢了还是被格式抑制了？", "a": "换探测方式重测：允许自由格式、few-shot 提示、或要求模型先推理再答；若能力恢复说明是被输出格式/拒答策略抑制（可调），仍差则是参数层面的真实遗忘（需回放重训）。"},
        ],
    },
    {
        "id": "posttrain-039",
        "topic": "评测与安全",
        "type": "八股",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["Anthropic", "OpenAI", "字节"],
        "years": ["2024", "2025"],
        "question": "红队测试怎么组织？越狱攻击有哪些类型，防御分层怎么做？",
        "answerMd": r'''**一句话核心**：红队 = 用对抗视角系统找漏洞（人工 + 自动化 + 外部众测），越狱手段围绕「角色扮演、编码混淆、多轮诱导、系统提示泄露、间接注入」；防御是分层纵深：训练层安全对齐、推理层系统提示与输入检测、输出层过滤与拒答，外加持续回归评测。

**1. 红队组织。** 内部专职团队 + 领域专家（安全、生物、化学、心理）+ 外部众测/漏洞赏金；先建威胁模型（谁、用什么能力、造成什么伤害），按风险域设计攻击面；自动化部分用对抗模型互相攻击（攻击者模型生成 prompt，目标模型响应，judge 判定是否越狱）规模化搜索；输出结构化发现：攻击路径、危害等级、复现步骤，进入修复-回归循环。

**2. 越狱类型。** 角色扮演/虚构框架（DAN 类）；任务伪装（翻译、续写、学术框架包裹违规请求）；渐进式多轮诱导（逐步升级上下文）；编码绕过（Base64、外语、字符插空、生僻隐喻）；系统提示抽取与注入（含 RAG 文档里的间接 prompt injection）；长上下文稀释注意力；还有针对思维链的引导泄露。

**3. 分层防御。** 训练层：安全 SFT + 偏好数据覆盖攻击样本、RLAIF 持续加固、宪法式原则约束；推理层：输入分类器（已知越狱模式）、系统提示防护、权限与工具调用沙箱；输出层：内容过滤、引用溯源；运营层：版本化安全回归集（新攻击入库即成为门禁）、灰度与快速回滚。要点：防御是概率性的，目标是抬高攻击成本与降低自动化成功率。''',
        "keyPoints": [
            "红队：威胁模型 → 人工+自动+众测 → 修复回归循环",
            "自动化红队：攻击模型与 judge 规模化搜索",
            "越狱五类：角色扮演/伪装/多轮诱导/编码混淆/注入",
            "纵深防御：训练加固、输入检测、输出过滤、回归门禁",
        ],
        "followUps": [
            {"q": "间接 prompt injection 为什么难防？", "a": "攻击载荷藏在模型要消费的正常内容里（网页、文档、邮件），输入侧无法简单区分「指令」与「数据」；需要输出侧行为约束（工具白名单、敏感操作二次确认）、来源标注与指令数据分离约定共同缓解。"},
        ],
    },
    {
        "id": "posttrain-040",
        "topic": "评测与安全",
        "type": "八股",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["Anthropic", "月之暗面", "阿里"],
        "years": ["2024", "2025"],
        "question": "什么是过度拒答（over-refusal）？怎么校准安全边界？",
        "answerMd": r'''**一句话核心**：过度拒答是模型把无害请求误判为有害而拒绝（安全对齐的假阳性），源于安全数据里「敏感关键词 → 拒答」的捷径；校准要靠双向数据（边界无害样本 + 真有害样本）、安全与可用性联合评测（如 XSTest 类基准）、以及拒答质量本身作为训练目标。

**1. 成因。** 安全训练数据的分布偏置：拒答样本集中在含敏感词的请求上，模型学到词面触发的拒答规则；RLHF 里 judge 对「拒答」给安全加分，强化了保守倾向；系统提示叠加多层安全指令加剧保守。后果是医疗、法律、写作等正当场景可用性受损，用户改用越狱绕过反而增加风险。

**2. 校准方法。** 数据层：构造「看似敏感实则无害」的边界样本（XSTest 思路：同形异义、历史/医学/创作语境）标记为应正常回答，同时保留真有害负样本让边界有区分度；标注规范写清「危害来自用途而非话题」；拒答样本也要高质量——说明原因并给出安全替代（部分拒答），把拒答当成一种生成任务训练。评测层：over-refusal 基准 + 正常任务回归双轨，安全集与可用性集设联合门禁（任一塌了都不发）。

**3. 工程细节。** 分级响应：完全拒答、部分回答 + 边界说明、安全完成（如创作类加免责）三种动作而不是二元；不同风险域（生物、隐私、自伤）阈值分开配置；线上监控拒答率突增作为回归信号。''',
        "keyPoints": [
            "过度拒答 = 安全假阳性，源于关键词捷径",
            "边界无害样本（XSTest 思路）+ 真有害样本双向覆盖",
            "拒答本身要训练：解释原因、给替代、分级响应",
            "安全与可用性双门禁，线上监控拒答率",
        ],
        "followUps": [
            {"q": "安全性和可用性冲突时怎么定发布标准？", "a": "按风险域分级而不是全局折中：高危域（生化武器、未成年人）安全优先零容忍；中低危域设可用性下限（如过度拒答率不超过某阈值）。用联合评测矩阵定位冲突样本，逐类决策并记录，避免拍脑袋全局调 β。"},
        ],
    },
    {
        "id": "posttrain-041",
        "topic": "评测与安全",
        "type": "八股",
        "difficulty": 4,
        "frequency": 3,
        "companies": ["DeepSeek", "月之暗面", "智谱"],
        "years": ["2025", "2026"],
        "question": "2025 到 2026 年对齐方法的格局有什么变化？RLVR 兴起后 SFT/DPO 的角色怎么变？",
        "answerMd": r'''**一句话核心**：格局从「SFT + 偏好对齐（RLHF/DPO）」转向「RLVR 可验证奖励 RL 为主引擎 + 偏好方法管风格与安全 + 蒸馏做普惠」：推理能力靠在线 RL 与测试时扩展驱动，DPO 系退守为轻量组件，评测重心从偏好榜转向可验证能力与 agent 任务。

**1. RLVR 成为主引擎。** 数学、代码、agentic 任务有天然校验器，0/1 结果奖励难被 hack、不需要 RM，R1-Zero 证明了纯 RL 可从基座直接激发长推理；2025 年起主流实验室的后训练算力大头转移到在线 RL（GRPO 及其变体 DAPO 等），传统「RM + PPO」更多保留在无法自动验证的领域（写作、对话质量、安全）。

**2. SFT/DPO 角色重定位。** SFT 变成管线里的「格式冷启动 + 能力蒸馏」环节；DPO 系用于偏好风格、语气、安全边界的快速迭代，以及作为 RL 前的廉价基线；两者从「对齐主力」降级为「组件」，但没消失——开放域没有可验证奖励，偏好数据仍是唯一信号源。

**3. 新焦点。** 测试时扩展（思考预算、并行采样与验证）让「训练-推理协同」成为对齐新维度；agent RL（工具调用、多轮环境）把对齐从单轮回答扩展到长程行为；安全上推理模型带来新攻击面（思维链被引导、思考过程泄露）。面试视角：被问对齐时要能说清「哪些目标适合 RLVR、哪些只能用偏好学习」的边界判断，这是当下最有信息量的能力信号。''',
        "keyPoints": [
            "RLVR 成为主引擎：可验证任务 + 规则奖励",
            "RM+PPO 保留在无法自动验证的领域",
            "SFT/DPO 降级为冷启动、蒸馏与风格组件",
            "新维度：测试时扩展、agent RL、思维链安全",
            "核心能力信号：RLVR 与偏好学习的适用边界判断",
        ],
        "followUps": [
            {"q": "哪些对齐目标永远不适合 RLVR？", "a": "没有客观真值的目标：文风与语气偏好、创意多样性、价值对齐、情感支持质量等——既无法写校验器，硬造规则奖励会被 hack；这类仍需人类偏好数据 + RM/偏好优化，两者是互补而非替代关系。"},
        ],
    },
    # ---------------------------------------------------------------- 工程选型
    {
        "id": "posttrain-042",
        "topic": "工程选型",
        "type": "场景",
        "difficulty": 4,
        "frequency": 4,
        "companies": ["阿里", "华为", "字节", "百度"],
        "years": ["2025", "2026"],
        "question": "业务要接入一个领域（如医疗、法律），RAG、SFT、继续预训练（CPT）怎么选？给决策树。",
        "answerMd": r'''**一句话核心**：按「需求类型」分流：知识查询与时效性 → RAG；输出风格、格式、流程行为 → SFT；领域语言与词表差异大到基座「读不懂」→ CPT；三者常组合，顺序是先 CPT 补语言、再 SFT 定行为、最后 RAG 挂知识。

**1. RAG 适用信号。** 知识频繁更新、需要可溯源、回答依赖私有文档、错误答案代价高；知识以检索形式外挂，模型不用改。局限：检索质量是天花板、长文档多跳推理弱、不改模型行为风格。

**2. SFT 适用信号。** 需求本质是「行为」：固定输出格式、领域话术、遵循业务流程、分类抽取等任务型工作；数据量几百到几十万都可以。局限：注入事实知识不可靠（容易幻觉、难更新），改知识别用它。

**3. CPT 适用信号。** 领域有大量未标注专业语料，且通用模型在该领域 loss 明显偏高（术语、缩写、文体差异大，如生物文献、代码库、小语种）；CPT 改变的是「语言基础」，对下游任务是乘法。代价高：要防遗忘（混通用语料）、要重做后训练全流程。

**4. 决策树与组合。** 先问：错误是因为「不知道」（检索可解 → RAG）还是「不会说/不会做」（行为 → SFT）还是「读不懂」（语言 → CPT）。典型组合：医疗场景 CPT（文献语料）→ SFT（诊疗报告格式、拒答边界）→ RAG（药品说明书与指南，保时效与溯源）；预算紧时 SFT + RAG 起步，用领域困惑度评测判断是否值得上 CPT。''',
        "keyPoints": [
            "知识时效溯源 → RAG；行为格式 → SFT；领域语言 → CPT",
            "SFT 注知识不可靠、难更新，RAG 检索质量是天花板",
            "CPT 判断依据：领域困惑度显著偏高 + 大量未标注语料",
            "组合顺序：CPT → SFT → RAG，各自职责分离",
        ],
        "followUps": [
            {"q": "怎么量化判断要不要做 CPT？", "a": "在领域语料上测基座困惑度，与通用语料对比差几个点；再做小规模 CPT 试点看 loss 下降幅度与下游任务增益是否显著，同时测通用基准损失是否可接受，用试点数据而不是直觉决定。"},
        ],
    },
    {
        "id": "posttrain-043",
        "topic": "工程选型",
        "type": "八股",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["字节", "阿里", "小米"],
        "years": ["2024", "2025"],
        "question": "chat template 有哪些实战中的坑？怎么系统性地避免？",
        "answerMd": r'''**一句话核心**：最大的坑是「训练与推理模板不一致」，其次是特殊 token 处理（BOS 重复、eos 缺失）、角色语义分歧（system 并入 user）、工具调用模板各家族不统一、以及 tokenization 边界（前后空格）问题；系统性对策是把模板当版本化代码资产 + 一致性单测。

**1. 高频事故清单。** BOS 重复添加（tokenizer 自带 add_bos 且模板又拼一次）；训练时 eos 计 loss、推理时没拼 eos 导致不停止（或反过来）；system prompt 有的模板并入首条 user、有的独立角色，跨模型迁移不改模板直接掉点；few-shot 拼接位置在 system 外导致格式漂移；tool/function call 的标记各家语法不同，跨家族复用数据会学出四不像；多轮 diff 式编码时把下一轮起始 token 误计 loss；中英文空格与换行的 token 边界在训练推理两侧不同。

**2. 系统性对策。** 模板收敛为单一实现（直接用 apply_chat_template 或自维护的版本化模板模块），训练、评测、推理引擎（vLLM 等要显式传模板）、日志回放四处共用；每个模型版本配「模板单测」：渲染后逐 token 比对特殊 token 序列、检查 eos 是否在、BOS 唯一性；数据构建时保留原始消息结构、渲染只在最后一步；跨模型训练数据存「消息列表」而非拼好的字符串。

**3. 排查方法。** 效果异常先看「训练样本的 decode 还原」和「推理请求的实际 token 序列」，肉眼比对 diff；大多数玄学掉点在这一步现形。''',
        "keyPoints": [
            "事故清单：BOS 重复、eos 缺失、system 语义、tool 模板差异",
            "模板版本化 + 训练/评测/推理单源共用",
            "数据存消息结构，渲染放最后一步",
            "模板单测：特殊 token 序列逐项断言",
            "排查从 decode 还原与实际请求 token diff 入手",
        ],
        "followUps": [
            {"q": "工具调用的模板设计有什么讲究？", "a": "工具 schema 的序列化要稳定（JSON 字段顺序固定、缩进一致），调用结果回填的边界要可 mask；训练数据里工具响应应有独立 role，模型学会「等结果再继续」的停止行为，否则会幻觉工具输出。"},
        ],
    },
    {
        "id": "posttrain-044",
        "topic": "工程选型",
        "type": "八股",
        "difficulty": 4,
        "frequency": 3,
        "companies": ["智谱", "MiniMax", "阶跃星辰"],
        "years": ["2024", "2025"],
        "question": "多模态模型的后训练和纯文本有什么不同？视觉指令数据怎么做？",
        "answerMd": r'''**一句话核心**：多模态后训练多了「视觉 token 与语言空间的接口对齐」问题：数据从纯问答扩展到图文交错、OCR、图表、定位、视频等多形态，训练要防视觉能力与文本能力互相挤占，模板与分辨率策略（动态 tile）引入新的工程坑。

**1. 接口与数据差异。** 视觉编码器输出经 projector 进入 LLM，后训练要同时顾及 projector 与 LLM 的适配；指令数据形态更多样：图像问答、多图对比、文档/图表理解（OCR+结构化）、grounding（坐标框输出）、视频时序理解、图文交错生成。典型构造：复用成熟感知模型的标注（检测/OCR 结果转问答）+ 强模型看图生成 + 人工精标覆盖长尾；负样本要有「图中没有答案」类问题防幻觉。

**2. 训练要点。** 常见两阶段：先 projector 对齐（冻 LLM 与视觉塔）再联合指令微调（部分放开视觉塔）；分辨率策略：动态高分辨率 tile 切分 + 缩略图，训练数据要覆盖不同 tile 组合；防遗忘：混入纯文本指令数据（比例常 10%~30%）防文本能力退化，混入图文数据防视觉对齐漂移。

**3. 评测与坑。** 评测分感知（计数、OCR、定位）与推理（图表问答、科学推理）双轴，再加纯文本回归；高频坑：位置编码在多图/长视频下的外推、坐标 token 化方式与训练不一致、视频帧采样策略训练推理不一致、纯文本任务被无谓插入图像占位符。''',
        "keyPoints": [
            "核心新问题：视觉 token 与语言空间的接口对齐",
            "数据形态：QA/文档/图表/grounding/视频/图文交错",
            "负样本防幻觉：图中无答案类问题必须覆盖",
            "两阶段训练 + 动态 tile 分辨率策略",
            "混纯文本数据防文本退化，感知推理双轴评测",
        ],
        "followUps": [
            {"q": "多模态模型为什么容易幻觉图中不存在的物体？", "a": "语言先验太强：模型基于文本常见搭配补全而非视觉证据；训练数据里大量「图配文」样本让文字模式成为捷径。缓解靠负样本、要求引用视觉证据的标注风格、grounding 监督以及解码时的视觉一致性校验。"},
        ],
    },
    {
        "id": "posttrain-045",
        "topic": "工程选型",
        "type": "概念",
        "difficulty": 3,
        "frequency": 3,
        "companies": ["面壁智能", "微软", "智谱"],
        "years": ["2024", "2025"],
        "question": "模型合并（model soup、TIES、DARE）是什么原理？什么条件下能合出更好的模型？",
        "answerMd": r'''**一句话核心**：模型合并把多个同底座微调模型的权重做算术组合：model soup 平均同任务不同超参的微调解，task arithmetic/TIES/DARE 处理跨任务的差值合并（符号冲突消解、冗余差值剪枝）；能成功的隐含前提是各模型共享预训练盆地——微调只做了小幅线性可组合的移动。

**1. 主要方法。** model soup：同一任务多个微调 run 的权重平均（沿损失面平坦方向找到更宽的解），zero-shot soup / greedy soup 按验证集贪心挑选；task arithmetic：$W_{merge} = W_{pretrain} + \lambda \sum_i \tau_i$（$\tau_i$ 为任务微调差值）；TIES：先修剪小幅差值（trim）、再消解符号冲突（elect，按差值幅度选主导符号）、最后平均；DARE：随机丢弃大部分差值并按丢弃率放大残余，降低任务间干扰；工具上 mergekit 是事实标准。

**2. 成功条件。** 强约束：同架构同词表、最好同预训练底座（不同底座的合并通常失败）；各微调不偏离底座太远（LoRA 差值更友好）；任务间不要求互斥的输出分布。合并前对齐表示（如 git re-basin 解决排列对称性）能提升成功率的场景也存在。

**3. 实用定位。** 适合：多任务能力叠加不想多部署、多 seed 平均提稳、把 RL 模型与通用 chat 模型混合（RL 强推理 + chat 泛化）；不适合：需要精确可控的单一任务、跨家族模型。合并后必须过完整评测（含安全回归），因为合并可能破坏单模型的安全对齐——这是常被忽略的坑。''',
        "keyPoints": [
            "soup：同任务多 run 平均；task arithmetic：差值加权叠加",
            "TIES：trim + 符号选举 + 平均；DARE：随机剪差值再缩放",
            "前提：同底座同架构，微调位移小且线性可组合",
            "典型用途：多能力叠加、多 seed 提稳、RL+chat 混合",
            "合并后要重过安全与通用回归",
        ],
        "followUps": [
            {"q": "为什么不同预训练底座的模型几乎不能合并？", "a": "两个底座在参数空间处于不同盆地，同名的权重没有对应语义（神经元排列不同），逐元素加权相当于混合不相关的方向；即使能力相似，差值向量也不可交换。理论上有排列对齐方案，但代价高且不保证成功。"},
        ],
    },
]

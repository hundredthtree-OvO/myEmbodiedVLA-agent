# docs 总览

这份目录说明 `docs/` 下各文档当前分别承担什么角色，避免后续讨论结果越积越散。

---

## 1. 当前文档分工

### [roadmap-detailed.md](/E:/my-embodied/docs/roadmap-detailed.md)
用途：

- 记录当前项目已经做到哪里
- 记录每一轮实现、真实仓库回归和阶段判断
- 作为“执行中路线图”和进度对齐文档

适合写入：

- 已完成的功能
- 最近一次验证结论
- 下一步最直接要做的事情

不适合写入：

- 过长的方法论讨论
- 太发散的长期愿景

### [issues-and-next-steps.md](/E:/my-embodied/docs/issues-and-next-steps.md)
用途：

- 记录当前暴露出来的工程问题
- 记录优先级和低成本解法
- 作为近中期问题清单

适合写入：

- 证据质量、prompt、cache、memory、paper ingestion 等问题
- 需要排期但尚未实现的工程改进

### [vision-and-learning-loop.md](/E:/my-embodied/docs/vision-and-learning-loop.md)
用途：

- 说明项目长期愿景
- 解释为什么它不只是论文读码工具
- 讨论交互层、知识层、长期学习闭环

适合写入：

- 产品方向
- 长期研究副驾定位
- 分阶段成长路径

### [paper-concept-structural-mapping.md](/E:/my-embodied/docs/paper-concept-structural-mapping.md)
用途：

- 讨论“论文显式概念、代码隐式实现”这类问题
- 说明为什么不能只靠关键词匹配
- 为 `bridge_attention`、`action_head`、`reasoning_tokens` 这类概念提供方法论

适合写入：

- 结构判据
- paper side / code side 的分层判断
- second-pass 如何围绕结构证据补片段

---

## 2. 当前推荐阅读顺序

如果想快速了解现在项目状态，推荐按这个顺序看：

1. [roadmap-detailed.md](/E:/my-embodied/docs/roadmap-detailed.md)  
   先看已经做到了什么、最近验证结论是什么

2. [issues-and-next-steps.md](/E:/my-embodied/docs/issues-and-next-steps.md)  
   再看当前主要问题、优先级和下一步工程切入点

3. [paper-concept-structural-mapping.md](/E:/my-embodied/docs/paper-concept-structural-mapping.md)  
   如果当前重点是 second-pass / Concept2Code 质量，再看这个

4. [vision-and-learning-loop.md](/E:/my-embodied/docs/vision-and-learning-loop.md)  
   最后看长期愿景和未来能力边界

---

## 3. 当前统一后的理解

截至目前，`docs/` 下几份文档已经基本形成这条主线：

1. 排序层已经从路径启发式，进化到 role-aware + AST rerank
2. second-pass 已经进入真实落地阶段
3. 当前主瓶颈从“选错文件”转到了“如何更精准地抽局部证据”
4. 对 `bridge_attention` 这类概念，后续不能再只靠关键词，而要做论文概念到代码结构的映射
5. 长期方向不是“继续堆模板”，而是让系统先理解论文，再决定去代码里验证什么

---

## 4. 后续建议的写法约定

为了避免重复和分散，后续建议这样维护：

- 新的实现结果、真实回归结论：优先写入 `roadmap-detailed.md`
- 新发现的问题和优先级：优先写入 `issues-and-next-steps.md`
- 新的方法论沉淀：优先写入 `paper-concept-structural-mapping.md`
- 长期产品/研究方向变化：优先写入 `vision-and-learning-loop.md`

如果某个讨论只会影响一个主题，就不要再单独新建文档。只有当它已经成为一个长期会反复引用的方法主题时，再拆成独立文档。

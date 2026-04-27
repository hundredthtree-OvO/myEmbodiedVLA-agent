ACoT-VLA: Action Chain-of-Thought for Vision-Language-Action Models
Linqing Zhong1,2 Yi Liu2 Yifei Wei1,2 Ziyu Xiong2
Maoqing Yao2∗ Si Liu1∗ Guanghui Ren2*
1Beihang University 2AgiBot
Abstract
Vision-Language-Action (VLA) models have emerged as
essential generalist robot policies for diverse manipula-
tion tasks, conventionally relying on directly translating
multimodal inputs into actions via Vision-Language Model
(VLM) embeddings. Recent advancements have introduced
explicit intermediary reasoning—such as sub-task predic-
tion (language) or goal image synthesis (vision)—to guide
action generation. However, these intermediate reason-
ing are often indirect and inherently limited in their ca-
pacity to convey the full, granular information required
for precise action execution. Instead, we posit that the
most effective form of reasoning is one that deliberates di-
rectly in the action space. We introduceAction Chain-
of-Thought (ACoT), a paradigm where the reasoning pro-
cess itself is formulated as a structured sequence of coarse
action intents that guide the final policy. In this paper,
we propose ACoT-VLA, a novel architecture that materi-
alizes the ACoT paradigm. Specifically, we introduce two
complementary components: an Explicit Action Reasoner
(EAR) and Implicit Action Reasoner (IAR). The former
proposes coarse reference trajectories as explicit action-
level reasoning steps, while the latter extracts latent ac-
tion priors from internal representations of multimodal in-
put, co-forming an ACoT that conditions the downstream
action head to enable grounded policy learning. Exten-
sive experiments in real-world and simulation environments
demonstrate the superiority of our proposed method, which
achieves98.5%,84.1%, and47.4%on LIBERO, LIBERO-
Plus and VLABench, respectively.
1. Introduction
To overcome the generalization limits of task-specific robot
policies [11, 48, 61], recent work has converged on Vision-
Language-Action (VLA) models [5, 24, 33, 41], which
always leverage a pre-trained Vision-Language Model
(VLM) [1, 2, 46] to encode visual and linguistic inputs into
*Corresponding author
(a) Pre-trained VLM Action Policy
Instruction
Sub-tasks
Observation
Actions
(b) World Model Action Policy
Instruction
Goal-image
Observation
Actions
(c) Pre-trained VLM Action Policy
Instruction Observation
Actions
Reference Actions
Figure 1. Chain-of-Thought in different space. (a) Language CoT
paradigm predicts sub-tasks as intermediate reasoning. (b) Visual
CoT paradigm synthesizes a goal image to provide guidance for
action policy. (c) Our proposed Action CoT directly operates in
action space and provides homogeneous action guidance.
a latent representation that conditions an action decoder.
Recent advancements seek to improve the mapping from
the input space to the action space by introducing the in-
termediate reasoning step by language generation, leading
to more generalized and precise action outputs [22, 53], as
visualized in Fig. 1(a). A parallel thrust leverages world
models [16, 50, 65] to simulate environmental dynamics, di-
rectly enhancing the efficacy and goal-oriented nature of the
generated action sequences [58, 62], as shown in Fig. 1(b).
Despite the promising trajectory set by these paradigms,
a critical challenge persists: existing generalist policies
think predominantly in the vision-language (input) space,
often failing to adequately address the inherent disparity
between these rich, semantic representations and the re-
quirements of precise, low-level action execution (output).
Specifically, the knowledge encoded within the VLM back-
bone of VLA models is derived from pre-training on web-
1
arXiv:2601.11404v1  [cs.RO]  16 Jan 2026

scale datasets focused on semantic alignment and question-
answering, yielding representations optimized for linguis-
tic understanding rather than physical dynamics. Similarly,
while world models forecast future visual states conditioned
on inputs, their guidance remains tethered to naturally vi-
sual representations. Crucially, both semantic and visual
forms of reasoning only offer suboptimal, indirect guid-
ance for generating the necessary action sequence. Con-
sequently, these prevailing approaches rely on an inherently
constrained information conduit, struggling to convey the
full, granular knowledge of the action space essential for
truly grounded and accurate robotic policy learning.
The inherent semantic-kinematic gap in existing poli-
cies,i.e., a fundamental disconnect between high-level, ab-
stract inputs and low-level, executable motor commands,
necessitates a paradigm shift in how guidance is provided.
We contend that to bridge this chasm, policies require
guidance that is kinematically coherent, rather than purely
semantic or visual. This core principle underpins our
novel framework:Action Chain-of-Thought (ACoT)(Fig.
1(c)). We redefine the “thought” process not as a sequence
of linguistic tokens, but as a structured chain of explicit,
kinematically-grounded action intents. This approach fur-
nishes the policy with direct motion cues, supplanting in-
direct representations. In a manner analogous to learning
from physical demonstration, this direct conditioning on
action-space information enables a substantially more ef-
ficient and veridically grounded policy learning process.
This foundational shift, however, introduces a critical
and distinct research challenge:“How can we robustly and
efficiently synthesize the complex, high-dimensional motion
cues required for ACoT reasoning from the raw, heteroge-
neous multimodal inputs?”
Action-related information manifests in two comple-
mentary forms,i.e., explicit or implicit. The explicit form
corresponds to observable motion trajectories, such as those
in human demonstrations, which directly encode executable
patterns of behavior. In contrast, the implicit form resides
in latent cues,e.g., linguistic expressions like “reach out”
or “grasp”, as well as interaction intents embedded in vi-
sual contexts. Although these cues are not presented as
explicit robotic trajectories, they implicitly define distribu-
tions over feasible actions within the action space. Building
upon this insight, we introduce two synergistic mechanisms
to generate both explicit and implicit guidance in the ac-
tion space. We first propose the Explicit Action Reasoner
(EAR), which is realized as a light-weight transformer. Par-
ticularly, EAR synthesizes coarse-grained motion trajecto-
ries conditioned on multimodal observations, offering direct
and executable guidance within the action space. Secondly,
we devise the Implicit Action Reasoner (IAR), which infers
latent action priors through applying cross-attention model-
ing between downsampled multimodal representations and
learnable queries, thereby providing implicit behavioral pri-
ors. Note that these two mechanisms are inherently comple-
mentary to each other. Subsequently, through jointly lever-
aging both EAR and IAR, we develop ACoT-VLA, an in-
tegrated Action Chain-of-Thought framework that enables
grounded generalist robot policy learning. Extensive exper-
iments across both real-world settings and three simulation
benchmarks consistently demonstrate the effectiveness and
versatility of our ACoT-VLA.
To summarize, our main contributions are as follows:
• Conceptually, we introduce Action Chain of Thought
(ACoT), a new paradigm for generalist robot policies. To
the best of our knowledge, this is the first work to formu-
late the deliberative process as a structured chain of ex-
plicit action-space intents, rather than abstract linguistic
or visual sub-goals.
• We delve into essential action space guidance and pro-
pose the Explicit and Implicit Action Reasoners, which
provide both explicit trajectory guidance and implicit be-
havioral inspiration for action prediction.
• Building upon these two modules, we further propose
ACoT-VLA, a unified framework for grounded general-
ist robot policy learning.
• Empirically, we validate our approach through exten-
sive simulation and real-world experiments, achieving
state-of-the-art performance on multiple benchmarks,i.e.,
98.5%, 84.1% and 47.4% on LIBERO, LIBERO-Plus and
VLABench, respectively.
2. Related Works
Vision-Language-Action Models.VLA models [14, 18,
19, 27] incorporate pre-trained VLM models to predict
language-driven robotic action sequences. Early works [24,
67] formulate robot control as an autoregressive sequence
generation problem, discretizing continuous actions into
bins. Inspired by generative modeling [31, 38, 66], increas-
ing works [5, 20, 33] adopt diffusion-based action policies
to synthesize smooth and high-quality action trajectories.
Given that robotic manipulation inherently occurs in three-
dimensional space, a line of studies [30, 52, 59] have sought
to enhance the spatial reasoning capability of VLA models
by integrating 3D priors. For instance, SpatialVLA [41] in-
tegrates spatial embeddings to endow model with 3D aware-
ness, while 4D-VLA [55] incorporates both spatial and tem-
poral information to enrich representations. Besides, due to
the scarcity of large-scale real-world robot demonstrations,
a series of efforts [6, 10, 12, 23, 37, 57] focus on data-
centric solutions, constructing large-scale robotic datasets
through simulation or real-world collection to scale up pol-
icy learning. Moreover, recent large-scale co-training ap-
proaches, such asπ 0.5 [22], GenieReasoner [35] and Gem-
ini Robotics [47], demonstrate the potential of unifying
web-scale language understanding with action learning, en-
2

Place the block
into the
 paper cup
(a) Explicit Action Reasoner
N ×️
(b) Implicit Action Reasoner
LLM
KV Cache
V Proj.
K Proj.
Text
Encoder
(c) Action-Guided Prediction
Cross-
Attention
Cross-
Attention
Pooling
&
Proj.
Self-Attention FFN
Self-
Attention
Action 
Head
Denoised
actions
Cross-Attention
Q Proj.
Proj. Proj.
Cross-Attention
Proj.
�ex
�im
at:t+Href−1
Visual
Encoder
Noise
at:t+H−1
Noise
Figure 2. Architectural Overview of ACoT-VLA. The framework consists of three main components operating on features from a shared
VLM backbone. (a) The Explicit Action Reasoner (EAR) is a Transformer-based module that synthesizes a coarse reference trajectory,
providing explicit action-space guidance. (b) The Implicit Action Reasoner (IAR) employs a cross-attention mechanism with learnable
queries to extract latent action priors from the VLM’s internal representations. (c) The Action-Guided Prediction (AGP) head synergisti-
cally integrates both explicit and implicit guidances via cross-attention to condition the final denoising process, producing the executable
action sequence.
hancing the policy’s generalization ability while retaining
the reasoning capability of pre-trained foundation models.
World-Model-based Policies.Advances in world mod-
els have demonstrated remarkable capability in synthesiz-
ing high-fidelity images and temporally coherent videos.
Building upon such progress, emerging researches [26, 29,
36, 56] exploit their predictive dynamics to implicitly guide
action generation. Specifically, CoT-VLA [60] introduces
visual chain-of-thought reasoning by forecasting sub-goal
images, explicitly integrating visual reasoning into action
prediction. WorldVLA [8] employs an autoregressive archi-
tecture that unifies perception and action generation within
a single framework. DreamVLA [58] extends beyond vi-
sual prediction and enriches world modeling with dynamic,
depth, and semantic cues, improving the model’s physical
consistency. Collectively, existing world-model-based ap-
proaches adopt a knowledge-forecasting perspective, incor-
porating primarily visual guidance into action trajectories
generation.
In contrast to previous works focusing on visual or lin-
guistic intermediaries for robotic policy learning, our key
insight lies in investigating guidance directly within the ac-
tion space, which intrinsically mitigates the heterogeneity
between perception and action, enabling the model to effec-
tively learn action-relevant priors.
3. Methodology
In this section, we present a detailed investigation into how
to generate effective action space guidance and integrate it
into robotic policy learning. We first define the robotic ma-
nipulation problem and formulate our proposed approach in
Sec. 3.1. The core of our method lies in two distinct action
reasoners introduced in Sec. 3.2 and Sec. 3.3, which pro-
vide explicit and implicit guidance within the action space.
We conclude by illustrating the policy prediction strategy
that effectively integrates this action guidance during pol-
icy learning (Sec. 3.4).
3.1. Problem Formulation
Given a natural language instructionland current visual ob-
servationo t, the generalist robot policyπ θ aims to predict
action sequencesa t:t+H−1 that accomplishes the specified
task. The process can be formally expressed as:
at:t+H−1 =π θ(ot, l),(1)
whereHrepresents the action horizon. Numerous works
introduce additional guidance signalsg, which encapsulates
various forms of auxiliary information to enhance policy’s
prediction ability. Specifically, these guidance signals can
be broadly categorized into two types: language-level guid-
anceg lang and vision-level guidanceg vis. The former is
primarily adopted by VLM-based methods,e.g., leverag-
ing LLMs’ reasoning capabilities to predict sub-tasks, while
the latter is always employed by world-model-based ap-
proaches, such as simulating future observations. Such re-
lationship can be formulated as:
πθ(at:t+H−1 , g|o t, l) =π θ(at:t+H−1 |o t, l, g)πθ(g|o t, l),
(2)
whereg∈ {g lang, g vis}. Conversely, we shift the focus to-
ward the action domain itself and investigate cues operating
directly in the action space, symbolized asgaction. The above
guidances are extended asg∈ {g lang, g vis, g action}.
3

Such action guidance can intuitively be disentangled into
explicit and implicit forms. The explicit guidanceg ex
action
provides direct priors in the form of reference action se-
quences, whereas the implicit guidanceg im
action arises from
contextual signals,e.g., action distribution inherently im-
plied in linguistics.
3.2. Explicit Action Reasoner
To incorporate explicit action trajectories into the thinking
process ofπ θ to generate high-quality action predictions,
we propose the Explicit Action Reasoner (EAR).
We design a mechanism that enables the model to au-
tonomously synthesize reference action sequences as inter-
nal guidance for policy learning. Analogously, this formu-
lation can be viewed as an action-space transfer of self-
conditioning in generative models [9, 34], where incorpo-
rating prior estimates into the generation process has been
shown to markedly improve sample quality. Building upon
this principle, we instantiate EAR as a light-weight trans-
former, as shown in Fig. 2 (a), generating kinematically
plausible action reference as explicit action-space guidance
gex
action for downstream action policy.
Formally, given visual observationo t and language in-
structionl, a pre-trained VLM encodes them into a contex-
tual key-value cache:
(KVLM
1:N , V VLM
1:N ) =VLM(o t, l),(3)
whereNrepresents the number of layers of VLM. Sub-
sequently, the EAR, denoted asπ ref
θ , takes a noisy action
sequence˜at:t+H ref −1 as input, whereH ref indicates the
horizon of reference actions. The sequence is first embed-
ded into an initial hidden representationh ref
0 , which serves
as the input to EAR’s transformer layers. At each trans-
former layeri, we adopt self-attention, along with cross-
attention with the contextual key-value cache from the cor-
responding VLM layer:
˜href
i =Self-Attn(h ref
i−1) +CrossAttn(h ref
i−1, KVLM
i , V VLM
i ),
(4)
where self-attention module captures temporal dependen-
cies within the action sequence and cross-attention mecha-
nism injects multimodal contextual priors from the VLM.
Then, the intermediate representation ˜href
i is processed by a
feed-forward network (FFN) in a residual-parallel manner,
updating thei-th EAR representationh ref
i :
href
i =h ref
i−1 +FFN( ˜href
i ).(5)
Through training via flow matching,π ref
θ learns a distri-
bution over action trajectories, producing a denoised action
sequence:
aref
t:t+H ref −1 =π ref
θ (˜at:t+H ref −1, KVLM
1:N , V VLM
1:N ).(6)
The generated sequence is then encoded via a MLP projec-
tor to obtain action embeddingZ ex, which serves as explicit
action-space guidanceg ex
action for action policy learning.
3.3. Implicit Action Reasoner
Beyond the explicit action trajectories, the multimodal la-
tent space of VLM also encodes implicit motion cues [13,
40],e.g., visual affordances and action-related semantics.
Effectively extracting these action-relevant representations
potentially offers complementary guidance. To this end,
we introduce an Implicit Action Reasoner (IAR), which di-
rectly operates on the VLM’s key–value cache.
Concretely, as presented in Fig. 2 (b), for each VLM
layeri∈[1, N], we initialize a learnable matrixQ i ∈
RM×d , whereMis a hyperparameter anddrepresents
VLM’s hidden dimension. Considering the information
redundancy within VLM’s key–value cache and computa-
tional efficiency, we first downsample the corresponding
key–value pairs into a lower-dimensional space, which is
formulated as:
Q′
i =Q iW (i)
Q , K ′
i =K VLM
i W (i)
K , V ′
i =V VLM
i W (i)
V ,
(7)
whereW (i)
Q , W (i)
K , W (i)
V ∈R d×d′
are learnable linear pro-
jectors andd ′ ≪d.
Later, cross-attention is applied to extract action-relevant
information from eachK ′
i andV ′
i . The resulting features
are subsequently integrated via average pooling and trans-
formed through a MLP projector, as visualized in Fig. 2 (b),
producing compact representations that capture the implicit
action semanticsz im
i embedded in VLM’si-th layer:
zim
i =MLP(Pool(CrossAttn(Q ′
i, K′
i, V ′
i ))).(8)
Then, through aggregating these representations across lay-
ers, we obtain implicit action-related featureZ im, which
serves as implicit action-space guidanceg im
action, comple-
menting the explicit motion priors.
3.4. Action-Guided Prediction
Building upon the explicit action embeddingZ ex produced
by EAR and implicit action-related featureZ im obtained in
IAR, in this section, we introduce the Action-Guided Pre-
diction (AGP) strategy to incorporate both action guidances
into policy learning.
As illustrated in Fig. 2 (c), given a noisy action segment
˜at:t+H−1, we first encode it into noisy action embedding via
a MLP projector. Particularly, unlike previous approaches
that directly feed this embedding into action headπ head
θ , we
treat it as action query, denoted asQ action, which interacts
with bothZ ex andZ im to retrieve complementary priors for
conditional prediction.
Specifically, we perform dual cross-attention operations:
Sex =CrossAttn(Q action, Zex, Zex),(9)
4

Methods Guidance Spatial Object Goal Long Avg.
SR↑Rank↓ SR↑Rank↓ SR↑Rank↓ SR↑Rank↓ SR↑Rank↓
Diffusion Policy [11] – 78.3 23 92.5 15 68.3 24 50.5 24 72.4 24
Octo [48] – 78.9 22 85.7 23 84.6 17 51.1 23 75.1 22
CoT-VLA [60] Visual 87.5 17 91.6 17 87.6 14 69.0 16 81.1 17
WorldVLA [8](256*256) Visual 85.6 19 89.0 20 82.6 19 59.0 19 79.1 18
WorldVLA [8](512*512) Visual 87.6 16 96.2 12 83.4 18 60.0 18 81.8 16
DreamVLA [58] Visual 97.5 7 94.0 13 89.5 12 89.5 10 92.6 11
UniVLA [49] Visual 95.4 11 98.8 2 93.6 9 94.0 4 95.5 8
F1 [36] Visual 98.2 4 97.8 8 95.4 8 91.3 8 95.7 7
GE-Act [29] Visual 98.2 4 97.6 9 95.8 6 94.4 3 96.5 5
TraceVLA [64] Linguistics 84.6 21 85.2 24 75.1 23 54.1 21 74.8 23
OpenVLA [24] Linguistics 84.7 20 88.4 21 79.2 20 53.7 22 76.5 21
UniAct [63] Linguistics 77.0 24 87.0 22 77.0 22 70.0 15 77.8 20
SpatialVLA [41] Linguistics 88.2 15 89.9 19 78.6 21 55.5 20 78.1 19
ThinkAct [17] Linguistics 88.3 14 91.4 18 87.1 15 70.9 14 84.4 15
π0-FAST [39] Linguistics 96.4 10 96.8 11 88.6 13 60.2 17 85.5 14
FPC-VLA [51] Linguistics 87.0 18 92.0 16 86.2 16 82.2 12 86.9 13
SmolVLA [43] Linguistics 93.0 13 94.0 13 91.0 11 77.0 13 88.8 12
GR00T-N1 [4] Linguistics 94.4 12 97.6 9 93.0 10 90.6 9 93.9 10
π0 [5] Linguistics 96.8 9 98.8 2 95.8 6 85.2 11 94.1 9
DD-VLA [28] Linguistics 97.2 8 98.6 4 97.4 4 92.0 7 96.3 6
MemoryVLA [42] Linguistics 98.4 3 98.4 5 96.4 5 93.4 5 96.7 4
π0.5[22] Linguistics 98.8 2 98.2 7 98.0 2 92.4 6 96.9 3
OpenVLA-OFT [25] Linguistics 97.6 6 98.4 5 97.9 3 94.5 2 97.1 2
Ours Action 99.4 1 99.6 1 98.8 1 96.0 1 98.5 1
Table 1. Comparison on the LIBERO benchmark. The best results are highlighted inbold. All metrics are average success rates (%).
Sim =CrossAttn(Q action, Zim, Zim),(10)
whereS ex andS im denote the attended representations
guided by explicit and implicit priors, respectively. Note
that although both encode action-relevant information, they
may highlight different facets of the underlying motion. For
instance, explicit priors provide kinematic cues, whereas
implicit priors capture latent action tendencies. Hence,
to effectively combine these complementary guidance, we
concatenate the two attended features and process them
through self-attention fusion block, which integrates the pri-
ors into a unified representation ¯h:
¯h=Self-Attn([S ex;S im]).(11)
Eventually, the aggregated representation¯his fed intoπ head
θ ,
which predicts the denoised action sequencea t:t+H−1.
Training Objectives.The entire framework is optimized
under a standard flow-matching mean-squared error (MSE)
objective. The training losses consist of two parts,i.e., flow-
matching MSE for both Explicit Action Reasonerπ ref
θ and
action headπ head
θ , denoted asL πref
θ
andL πhead
θ
, respectively.
Hence, the overall objective is:
Ltotal =λ 1Lπref
θ
+λ 2Lπhead
θ
,(12)
whereλ 1 andλ 2 are balance factors.
Teacher Forcing Stabilization.During training, the out-
puts ofπ ref
θ can be unstable. To stabilize optimization,
we computeZ ex directly from ground-truth reference tra-
jectories instead of fromπ ref
θ predictions, preventing opti-
mization interference toπ head
θ . During inference, the model
switches to a fully self-conditioned mode, whereπ ref
θ au-
tonomously generates the reference actions to guideπ head
θ
in action prediction.
4. Experiments
In this section, we first outline the experimental setup in
Sec. 4.1. Then, in Sec. 4.2, we evaluate our approach on
three simulation benchmarks, followed by comprehensive
ablation studies in Sec. 4.3. Moreover, we present real-
world deployment results in Sec. 4.4 to evaluate real-world
applicability.
4.1. Experimental Setup
Data Sources.For simulation experiments, we strictly
follow the official training splits provided by the corre-
sponding benchmark (LIBERO [32], LIBERO-Plus [15],
and VLABench [57]), and train our models exclusively on
their standard demonstration datasets without introducing
any additional data. For the real-world setting, all demon-
strations used for model training are collected on our own
robotic platform. More details about data sources are intro-
duced in Appendix A.
Implementation Details.We implement our approach
uponπ 0.5 [22]. Specifically, we adopt SigLIP [54] as the
visual encoder, while the LLM backbone is instantiated as
Gemma 2B architecture [3] withN= 18layers and hidden
sized= 2048. For frame processing, each input frame is
resized to224×224prior to the visual encoder. Regarding
5

Methods Guidance Camera Robot Language Light Background Noise Layout Avg.
WorldVLA [8] Visual 0.1 27.9 41.6 43.7 17.1 10.9 38.0 25.0
OpenVLA [24] Linguistics 0.8 3.5 23.0 8.1 34.8 15.2 28.5 15.6
NORA [21] Linguistics 2.2 37.0 65.1 45.7 58.6 12.8 62.1 39.0
UniVLA [7] Linguistics 1.8 46.2 69.6 69.0 81.0 21.2 31.9 42.9
π0-Fast [39] Linguistics 65.1 21.6 61.0 73.2 73.2 74.4 68.8 61.6
RIPT-VLA [44] Linguistics 55.2 31.2 77.6 88.4 91.6 73.5 74.2 68.4
OpenVLA-OFT [25] Linguistics 56.4 31.9 79.5 88.7 93.3 75.8 74.2 69.6
OpenVLA-OFT+ [15] Linguistics 92.830.385.894.9 93.989.377.6 79.6
π∗0 [5] Linguistics 79.6 21.1 72.5 84.7 86.2 68.3 69.4 67.4
π∗0.5[22] Linguistics 70.3 41.7 81.197.3 94.671.884.9 75.7
Ours Action 91.2 62.5 80.3 95.1 91.5 88.3 84.9 84.1
Table 2. Performance comparison on the LIBERO-Plus benchmark. Best results are highlighted in bold. An asterisk (*) denotes results
reproduced by us for fair comparison.
the EAR, we employ a compact Transformer-based design
composed ofN= 18layers. Concerning the IAR, each
learnable query matrixQ i is configured with a row dimen-
sion ofM= 1. The reduced dimension in the downsam-
pling strategy is set tod ′ = 128.
In terms of model training, unless explicitly specified,
the horizon of predicted reference actionsH ref and action
policy outputHare fixed to15and10, with action shift set
to2and1, respectively. To clarify, the action shift specifies
the temporal interval relative to the expert demonstration.
For instance, a shift of1yields frame-aligned predictions,
whereas a shift of2skips one intermediate frame. We set
the balance factors in training losses asλ 1 =λ 2 = 0.5.
Training Configuration.We adopt a unified set of train-
ing hyperparameters across all experiments unless explicitly
specified. Concretely, the learning rate follows a cosine-
decay schedule with a warm-up phase of10K steps, a
peak learning rate of5e−5, and a decay toward5e−5over
10K steps. Optimization is performed with AdamW with
gradient-norm clipping set to1.0. An exponential moving
average (EMA) of model parameters is maintained with a
decay rate of0.999. Regarding hardware settings, model
training is performed on a single node equipped with8
NVIDIA H100 GPUs using bfloat16 precision. And the in-
ference is conducted on a single NVIDIA RTX 4090.
4.2. Simulation Experiments
In this section, we conduct the simulation evaluations across
three benchmarks,i.e., LIBERO [32], LIBERO-Plus [15],
and VLABench [57], to comprehensively evaluate our ap-
proach’s performance and generalization capabilities under
diverse task structures.
LIBERO Benchmark.LIBERO is a widely adopted sim-
ulation benchmark for evaluating generalist robotic poli-
cies. It consists of four task suites,i.e., LIBERO-Spatial,
LIBERO-Object, LIBERO-Goal, and LIBERO-Long. It is
designed to probe a different aspect of policy capability,
including spatial awareness, object-centric manipulation,
goal completion, and long-horizon reasoning. Each suite
consists of10tasks and provides50human-teleoperated
demonstrations per task for policy training. Following the
official evaluation protocol, we evaluate our policy on all
tasks within the benchmark. For each task, the policy is
evaluated over50independent trials, resulting in500roll-
outs in total.
As reported in Table 1, the quantitative evaluation results
demonstrate that our proposed approach outperforms exist-
ing methods across all tracks. Compared to the previous
state-of-the-art methodπ 0.5, our approach achieves a1.6%
absolute improvement in average success rate, highlight-
ing the clear advantages of incorporating action-space guid-
ance. Notably, we observe a pronounced improvement on
the LIBERO-Long suite, where tasks require long-horizon
manipulation with strict error control. We attribute this ad-
vantage to the nature of our proposed ACoT. Particularly,
unlike language- or vision-CoT, whose intermediate reason-
ing remains abstract or indirect with respect to action ex-
ecution, our proposed ACoT naturally operates in precise
representation. Through leveraging actions as intermedi-
ate reasoning tokens, the model feeds the following action
head with structured and fine-grained guidance, which sig-
nificantly enhances the robustness to error accumulation in
long-horizon manipulation tasks.
LIBERO-Plus Benchmark.Built upon LIBERO,
LIBERO-Plus is an extended robustness-oriented bench-
mark, designed to systematically evaluate generalist robotic
policies under controlled distribution shifts. Concretely,
LIBERO-Plus introduces7perturbation dimensions,
i.e., camera-viewpoints, robot-initial-states, language-
variations, lighting-conditions, background-textures,
sensor-noise and object-layout, which aim to expose
hidden failure modes under standard evaluations. Notably,
LIBERO-Plus consists of10,030evaluation episodes,
providing statistically reliable evaluation.
Following standard training configuration in LIBERO-
Plus [15] , we train our policy on the provided training set
for a total of100K optimization steps. In terms of evalu-
ation, we adhere to the protocol established in the bench-
6

Methods Guidance In-dist. Category Commonsense Instruction Texture Avg.
IS↑PS↑ IS↑PS↑ IS↑PS↑ IS↑PS↑ IS↑PS↑ IS↑PS↑
π0 [5] Linguistics 67.8 62.7 44.0 33.6 54.943.0 58.038.7 50.6 42.5 55.0 44.1
π0.5 [22] Linguistics 75.0 60.8 49.6 35.3 57.541.6 57.1 30.3 62.0 47.4 60.2 43.1
Ours Action 79.8 66.1 54.1 38.9 52.3 37.8 56.8 39.6 74.6 54.6 63.5 47.4
Table 3. Comparison on the VLABench benchmark. IS and PS represent Intention score and Progress score, respectively.
Name EAR IAR Spatial Object Goal Long Avg.
Baseline 98.8 98.2 98.0 92.4 96.9
#1 ✓ 99.0 99.4 98.096.6 98.3
#2 ✓ 99.2 99.2 98.2 95.6 98.1
#3 ✓ ✓ 99.4 99.6 98.896.0 98.5
Table 4. Module ablations. The performance is gradually im-
proved with the continuous addition of proposed methods.
mark,i.e., each episode is executed once without repeated
rollouts. Note that the average success rate is computed over
the entire evaluation set.
As shown in Table 2, our method significantly boosts the
policy’s performance, surpassing all previous methods by a
huge margin. In particular, our approach demonstrates pro-
nounced robustness under challenging perturbations such as
camera-viewpoint shifts (+11.6%), robot initial-state per-
turbations (+16.3%), and sensor noise (+12.5%), where
existing language-guided or vision-guided policies exhibit
significant degradation. These results highlight the effec-
tiveness of our action-space guidance in improving general-
ization under diverse perturbation factors.
VLABench Benchmark.VLABench is a large-scale eval-
uation suite aimed at benchmarking both VLAs and VLMs
on diverse robotic tasks. Built on ManiSkill3 [45], its
manipulation benchmark consists of various tabletop sce-
narios,e.g., contact-rich interactions and articulated-object
manipulation. The standard evaluation is organized into
5public tracks,i.e., in-distribution, cross-category, com-
monsense, semantic-instruction, and unseen-texture, which
respectively assess standard in-distribution performance,
category-level generalization, commonsense reasoning, in-
struction understanding, and robustness to appearance vari-
ations. Particularly, VLABench proposes Intention Score
(IS) and Progress Score (PS) to evaluate robot policies.
In our context, we trainπ 0,π 0.5, along with our method
in a unified training setup. The model training is performed
on VLABench’s official training data, with a global batch
size128. All models are optimized for60K steps. We
present quantitative results in Table 3. Overall, our method
achieves the best performance across both IS and PS. No-
tably, under the unseen-texture track, it delivers substan-
tial gains,i.e.,+12.6%in IS and+7.2%in PS, indicating
strong robustness to distributional shifts. Together, these
results further confirm the effectiveness of our proposed ap-
proach.
Name Action
shift
Action
horizon
Equi.
horizonSpatial Object Goal LongAvg.
Baseline 1 10 10 98.6 99.0 96.4 92.2 96.6
1 10 10 99.4 99.498.895.0 98.2
2 5 10 99.6 99.698.4 94.4 98.0
1 30 30 99.2 99.2 97.6 95.6 97.9
+EAR 2 15 30 99.0 99.4 98.096.6 98.3
2 30 60 99.4 99.0 98.2 95.0 97.9
3 30 90 98.8 99.4 97.4 96.2 98.0
Table 5. Reference action parameter ablation. We observe that dif-
ferent reference-action configurations within EAR generally lead
to performance improvements.
Methods Spatial Object Goal Long Avg.
Baseline 98.8 98.2 98.0 92.4 96.9
Query 98.8 99.0 97.2 92.8 97.0
Attention Pooling 99.498.698.292.8 97.3
Downsample 99.299.2 98.2 95.6 98.1
Table 6. Comparison of KV-cache interaction strategies in IAR.
4.3. Ablation Study
We examine each component’s contribution via systematic
ablation experiments on the LIBERO benchmark, which are
shown in Table 4, Table 5, and Table 6. Note that we adopt
π0.5 as the “Baseline” method. More ablations in different
benchmarks are in Appendix C.
EAR.As shown in Table 4, compared with the baseline, the
experiment “#1” introduces the Explicit Action Reasoner
(EAR) module into policy learning, which lifts the average
success rate from96.9%to98.3%, demonstrating that the
explicit action-space guidance benefits the robotic action se-
quence prediction. A plausible explanation is that EAR in-
troduces an intermediate reference action sequence, which
injects strong inductive bias on the behavior and thereby re-
duces ambiguity in mapping from observations to actions.
IAR.Analogously, with the Implicit Action Reasoner
(IAR) module added in “#2”, the average success rate in-
creases from96.9%to98.1%. This gain suggests that
exploiting the implicit action distribution encoded in vi-
sion–language representations can also provide effective
guidance for policy learning. This performance gain can be
partly attributed to the fact that IAR distills action-related
clues implicitly encoded within the vision–language back-
bone, which potentially reflects the distribution of feasible
actions. Such priors encourages the policy to remain closer
to coherent, task-consistent behavioral patterns.
EAR + IAR.In Table 4, experiment “#3” incorporates both
EAR and IAR, achieving the highest average success rate
7

Wipe the stain on the table
Pour water into the cup
Pick up the blue doll  
Figure 3. Visualization of three manipulation tasks in real world.
of98.5%. The consistent improvements demonstrate that
explicit action guidance and implicit action cues extracted
from VLM’s key-value cache are complementary, jointly
providing stronger guidance for accurate action prediction.
Reference Action Configurations.To further examine the
effect of explicit action references in EAR, we investigate
different settings of action shift and action horizon, as sum-
marized in Table 5. We observe various parameter combi-
nations consistently bring improvements over the baseline,
indicating that providing action cues is broadly beneficial
for policy learning. Besides, we find that shorter horizons
combined with moderate shifts tend to produce relatively
stronger gains. These observations offer further insight into
how explicit action guidance influence policy learning.
KV-cache Interaction Strategies.We compare three
strategies for extracting action-relevant cues from VLM’s
key-value cache within IAR module, as presented in Ta-
ble 6. Concretely, “Query” method uses learnable queries to
attend to VLM’s original key-value cache. “Attention Pool-
ing” method forms a pooled query by averaging key-value
cache and then applies cross-attention operation. “Down-
sample” method first downsamples VLM’s key-value cache
and then aggregates them using learnable matrix.
As shown in Table 6, all three variants outperform the
baseline, indicating that extracting implicit action cues from
VLM benefits policy learning. Notably, the “Downsam-
ple” strategy achieves the best performance, suggesting
that VLM’s features may contain noisy information for ac-
tion prediction. This also highlights the importance of de-
signing appropriate interaction mechanisms to align vision-
language and action.
4.4. Real-World Deployment
To further validate the effectiveness of our framework, we
conduct extensive real-world experiments on the AgiBot G1
robot. We consider three manipulation tasks,i.e., “Wipe
Stain”, “Pour Water”, and “Open-set Pick”, which respec-
Figure 4. Evaluation results of real-world experiments.
tively assess contact-rich manipulation, fine-grained object
handling, and instruction-following abilities.
Specifically, as visualized in Fig. 3, the “Wipe Stain”
task requires the robot to pick up a sponge from the table
and wipe away the stain until the surface is clean. The “Pour
Water” task requires the robot to grasp the kettle by its han-
dle, locate the target cup, pour water into it without causing
overflow, and finally return the kettle to the table in a sta-
ble manner. The “Open-set Pick” task instructs the robot
to pick up the correct tabletop object according to given
natural-language command. Additionally, to examine the
cross-embodiment adaptability, we also perform the “Open-
set Pick” task on the AgileX robotic platform. Details about
training and evaluation are provided in the Appendix B.
As shown in Fig. 4, our approach achieves consistently
higher average success rates than bothπ 0.5 andπ 0,i.e.,
66.7%against61.0%and33.8%. These results demonstrate
that the proposed framework maintains effectiveness under
real-world sensing conditions. Moreover, the aligned im-
provements observed on both Agibot G1 and AgileX also
indicate that our method exhibits adaptability across differ-
ent robotic embodiments.
5. Conclusion
In this work, we addressed the fundamental semantic-
kinematic gap in modern robotic policies by proposing a
new paradigm: Action Chain-of-Thought (ACoT). We ar-
gued that for physically grounded intelligence, deliberation
should occur not in the abstract space of language or vi-
sion, but directly in the kinematically grounded space of
actions. We materialized this concept in our ACoT-VLA
framework, which leverages two synergistic modules,i.e.,
an Explicit Action Reasoner (EAR) and an Implicit Ac-
tion Reasoner (IAR), to generate and fuse both explicit tra-
jectory plans and implicit behavioral priors. This action-
centric guidance mechanism creates a direct, information-
rich conduit between high-level intent and low-level motor
control. Our extensive experiments across multiple simu-
lation and real-world benchmarks demonstrate that this ap-
proach yields state-of-the-art performance, significantly im-
8

proving both task success and robustness. By shifting the
locus of reasoning from perception to action, our work not
only provides a more effective and grounded method for
robot policy learning but also opens a new avenue for re-
search into more structured, interpretable, and capable em-
bodied agents. We believe that learning to “think” in the
language of actions is a critical step towards developing the
next generation of generalist robots.
References
[1] Josh Achiam, Steven Adler, Sandhini Agarwal, Lama Ah-
mad, Ilge Akkaya, Florencia Leoni Aleman, Diogo Almeida,
Janko Altenschmidt, Sam Altman, Shyamal Anadkat, et al.
Gpt-4 technical report.arXiv preprint arXiv:2303.08774,
2023. 1
[2] Shuai Bai, Keqin Chen, Xuejing Liu, Jialin Wang, Wenbin
Ge, Sibo Song, Kai Dang, Peng Wang, Shijie Wang, Jun
Tang, et al. Qwen2. 5-vl technical report.arXiv preprint
arXiv:2502.13923, 2025. 1
[3] Lucas Beyer, Andreas Steiner, Andr ´e Susano Pinto, Alexan-
der Kolesnikov, Xiao Wang, Daniel Salz, Maxim Neumann,
Ibrahim Alabdulmohsin, Michael Tschannen, Emanuele
Bugliarello, et al. Paligemma: A versatile 3b vlm for trans-
fer.arXiv preprint arXiv:2407.07726, 2024. 5
[4] Johan Bjorck, Fernando Casta ˜neda, Nikita Cherniadev,
Xingye Da, Runyu Ding, Linxi Fan, Yu Fang, Dieter Fox,
Fengyuan Hu, Spencer Huang, et al. Gr00t n1: An open
foundation model for generalist humanoid robots.arXiv
preprint arXiv:2503.14734, 2025. 5
[5] Kevin Black, Noah Brown, Danny Driess, Adnan Es-
mail, Michael Equi, Chelsea Finn, Niccolo Fusai, Lachy
Groom, Karol Hausman, Brian Ichter, et al.π 0: A vision-
language-action flow model for general robot control. corr,
abs/2410.24164, 2024. doi: 10.48550.arXiv preprint
ARXIV .2410.24164. 1, 2, 5, 6, 7
[6] Qingwen Bu, Jisong Cai, Li Chen, Xiuqi Cui, Yan Ding,
Siyuan Feng, Shenyuan Gao, Xindong He, Xuan Hu, Xu
Huang, et al. Agibot world colosseo: A large-scale manip-
ulation platform for scalable and intelligent embodied sys-
tems.arXiv preprint arXiv:2503.06669, 2025. 2
[7] Qingwen Bu, Yanting Yang, Jisong Cai, Shenyuan Gao,
Guanghui Ren, Maoqing Yao, Ping Luo, and Hongyang Li.
Univla: Learning to act anywhere with task-centric latent ac-
tions, 2025. 6
[8] Jun Cen, Chaohui Yu, Hangjie Yuan, Yuming Jiang, Siteng
Huang, Jiayan Guo, Xin Li, Yibing Song, Hao Luo, Fan
Wang, et al. Worldvla: Towards autoregressive action world
model.arXiv preprint arXiv:2506.21539, 2025. 3, 5, 6
[9] Ting Chen, Ruixiang Zhang, and Geoffrey Hinton. Analog
bits: Generating discrete data using diffusion models with
self-conditioning.arXiv preprint arXiv:2208.04202, 2022. 4
[10] Tianxing Chen, Zanxin Chen, Baijun Chen, Zijian Cai, Yibin
Liu, Zixuan Li, Qiwei Liang, Xianliang Lin, Yiheng Ge,
Zhenyu Gu, et al. Robotwin 2.0: A scalable data gen-
erator and benchmark with strong domain randomization
for robust bimanual robotic manipulation.arXiv preprint
arXiv:2506.18088, 2025. 2
[11] Cheng Chi, Zhenjia Xu, Siyuan Feng, Eric Cousineau, Yilun
Du, Benjamin Burchfiel, Russ Tedrake, and Shuran Song.
Diffusion policy: Visuomotor policy learning via action dif-
fusion.The International Journal of Robotics Research, 44
(10-11):1684–1704, 2025. 1, 5
[12] Shengliang Deng, Mi Yan, Songlin Wei, Haixin Ma, Yuxin
Yang, Jiayi Chen, Zhiqi Zhang, Taoyu Yang, Xuheng Zhang,
Wenhao Zhang, et al. Graspvla: a grasping foundation model
pre-trained on billion-scale synthetic action data.arXiv
preprint arXiv:2505.03233, 2025. 2
[13] Danny Driess, Fei Xia, Mehdi SM Sajjadi, Corey Lynch,
Aakanksha Chowdhery, Ayzaan Wahid, Jonathan Tompson,
Quan Vuong, Tianhe Yu, Wenlong Huang, et al. Palm-e: An
embodied multimodal language model. 2023. 4
[14] Jiafei Duan, Wentao Yuan, Wilbert Pumacay, Yi Ru Wang,
Kiana Ehsani, Dieter Fox, and Ranjay Krishna. Manipulate-
anything: Automating real-world robots using vision-
language models.arXiv preprint arXiv:2406.18915, 2024.
2
[15] Senyu Fei, Siyin Wang, Junhao Shi, Zihao Dai, Jikun Cai,
Pengfang Qian, Li Ji, Xinzhe He, Shiduo Zhang, Zhaoye Fei,
et al. Libero-plus: In-depth robustness analysis of vision-
language-action models.arXiv preprint arXiv:2510.13626,
2025. 5, 6, 12
[16] David Ha and J ¨urgen Schmidhuber. World models.arXiv
preprint arXiv:1803.10122, 2(3), 2018. 1
[17] Chi-Pin Huang, Yueh-Hua Wu, Min-Hung Chen, Yu-
Chiang Frank Wang, and Fu-En Yang. Thinkact: Vision-
language-action reasoning via reinforced visual latent plan-
ning.arXiv preprint arXiv:2507.16815, 2025. 5
[18] Siyuan Huang, Haonan Chang, Yuhan Liu, Yimeng Zhu,
Hao Dong, Peng Gao, Abdeslam Boularias, and Hongsheng
Li. A3vlm: Actionable articulation-aware vision language
model.arXiv preprint arXiv:2406.07549, 2024. 2
[19] Wenlong Huang, Chen Wang, Yunzhu Li, Ruohan Zhang,
and Li Fei-Fei. Rekep: Spatio-temporal reasoning of rela-
tional keypoint constraints for robotic manipulation.arXiv
preprint arXiv:2409.01652, 2024. 2
[20] Wenhui Huang, Changhe Chen, Han Qi, Chen Lv, Yilun
Du, and Heng Yang. Motvla: A vision-language-action
model with unified fast-slow reasoning.arXiv preprint
arXiv:2510.18337, 2025. 2
[21] Chia-Yu Hung, Qi Sun, Pengfei Hong, Amir Zadeh, Chuan
Li, U Tan, Navonil Majumder, Soujanya Poria, et al. Nora: A
small open-sourced generalist vision language action model
for embodied tasks.arXiv preprint arXiv:2504.19854, 2025.
6
[22] Physical Intelligence, Kevin Black, Noah Brown, James
Darpinian, Karan Dhabalia, Danny Driess, Adnan Esmail,
Michael Equi, Chelsea Finn, Niccolo Fusai, et al.π 0.5: a
vision-language-action model with open-world generaliza-
tion.arXiv preprint arXiv:2504.16054, 2025. 1, 2, 5, 6,
7, 13
[23] Tao Jiang, Tianyuan Yuan, Yicheng Liu, Chenhao Lu, Jian-
ning Cui, Xiao Liu, Shuiqi Cheng, Jiyang Gao, Huazhe Xu,
and Hang Zhao. Galaxea open-world dataset and g0 dual-
system vla model.arXiv preprint arXiv:2509.00576, 2025.
2
9

[24] Moo Jin Kim, Karl Pertsch, Siddharth Karamcheti, Ted Xiao,
Ashwin Balakrishna, Suraj Nair, Rafael Rafailov, Ethan
Foster, Grace Lam, Pannag Sanketi, et al. Openvla: An
open-source vision-language-action model.arXiv preprint
arXiv:2406.09246, 2024. 1, 2, 5, 6
[25] Moo Jin Kim, Chelsea Finn, and Percy Liang. Fine-tuning
vision-language-action models: Optimizing speed and suc-
cess.arXiv preprint arXiv:2502.19645, 2025. 5, 6
[26] Hengtao Li, Pengxiang Ding, Runze Suo, Yihao Wang, Zirui
Ge, Dongyuan Zang, Kexian Yu, Mingyang Sun, Hongyin
Zhang, Donglin Wang, et al. Vla-rft: Vision-language-action
reinforcement fine-tuning with verified rewards in world
simulators.arXiv preprint arXiv:2510.00406, 2025. 3
[27] Xiaoqi Li, Mingxu Zhang, Yiran Geng, Haoran Geng, Yux-
ing Long, Yan Shen, Renrui Zhang, Jiaming Liu, and Hao
Dong. Manipllm: Embodied multimodal large language
model for object-centric robotic manipulation. InProceed-
ings of the IEEE/CVF Conference on Computer Vision and
Pattern Recognition, pages 18061–18070, 2024. 2
[28] Zhixuan Liang, Yizhuo Li, Tianshuo Yang, Chengyue Wu,
Sitong Mao, Liuao Pei, Xiaokang Yang, Jiangmiao Pang,
Yao Mu, and Ping Luo. Discrete diffusion vla: Bringing dis-
crete diffusion to action decoding in vision-language-action
policies.arXiv preprint arXiv:2508.20072, 2025. 5
[29] Yue Liao, Pengfei Zhou, Siyuan Huang, Donglin Yang,
Shengcong Chen, Yuxin Jiang, Yue Hu, Jingbin Cai, Si Liu,
Jianlan Luo, et al. Genie envisioner: A unified world foun-
dation platform for robotic manipulation.arXiv preprint
arXiv:2508.05635, 2025. 3, 5
[30] Tao Lin, Gen Li, Yilei Zhong, Yanwen Zou, Yuxin Du, Jiting
Liu, Encheng Gu, and Bo Zhao. Evo-0: Vision-language-
action model with implicit spatial understanding.arXiv
preprint arXiv:2507.00416, 2025. 2
[31] Yaron Lipman, Ricky TQ Chen, Heli Ben-Hamu, Maximil-
ian Nickel, and Matt Le. Flow matching for generative mod-
eling.arXiv preprint arXiv:2210.02747, 2022. 2
[32] Bo Liu, Yifeng Zhu, Chongkai Gao, Yihao Feng, Qiang Liu,
Yuke Zhu, and Peter Stone. Libero: Benchmarking knowl-
edge transfer for lifelong robot learning.Advances in Neural
Information Processing Systems, 36:44776–44791, 2023. 5,
6, 12
[33] Songming Liu, Lingxuan Wu, Bangguo Li, Hengkai Tan,
Huayu Chen, Zhengyi Wang, Ke Xu, Hang Su, and Jun Zhu.
Rdt-1b: a diffusion foundation model for bimanual manipu-
lation.arXiv preprint arXiv:2410.07864, 2024. 1, 2
[34] Yunzhe Liu, Rinon Gal, Amit H Bermano, Baoquan Chen,
and Daniel Cohen-Or. Self-conditioned generative ad-
versarial networks for image editing.arXiv preprint
arXiv:2202.04040, 2022. 4
[35] Yi Liu, Sukai Wang, Dafeng Wei, Xiaowei Cai, Linqing
Zhong, Jiange Yang, Guanghui Ren, Jinyu Zhang, Maoqing
Yao, Chuankang Li, et al. Unified embodied vlm reason-
ing with robotic action via autoregressive discretized pre-
training.arXiv preprint arXiv:2512.24125, 2025. 2
[36] Qi Lv, Weijie Kong, Hao Li, Jia Zeng, Zherui Qiu, Delin
Qu, Haoming Song, Qizhi Chen, Xiang Deng, and Jiang-
miao Pang. F1: A vision-language-action model bridg-
ing understanding and generation to actions.arXiv preprint
arXiv:2509.06951, 2025. 3, 5
[37] Abby O’Neill, Abdul Rehman, Abhiram Maddukuri, Ab-
hishek Gupta, Abhishek Padalkar, Abraham Lee, Acorn Poo-
ley, Agrim Gupta, Ajay Mandlekar, Ajinkya Jain, et al. Open
x-embodiment: Robotic learning datasets and rt-x models:
Open x-embodiment collaboration 0. In2024 IEEE Inter-
national Conference on Robotics and Automation (ICRA),
pages 6892–6903. IEEE, 2024. 2
[38] William Peebles and Saining Xie. Scalable diffusion models
with transformers. InProceedings of the IEEE/CVF inter-
national conference on computer vision, pages 4195–4205,
2023. 2
[39] Karl Pertsch, Kyle Stachowicz, Brian Ichter, Danny Driess,
Suraj Nair, Quan Vuong, Oier Mees, Chelsea Finn, and
Sergey Levine. Fast: Efficient action tokenization for vision-
language-action models.arXiv preprint arXiv:2501.09747,
2025. 5, 6
[40] Shengyi Qian, Weifeng Chen, Min Bai, Xiong Zhou,
Zhuowen Tu, and Li Erran Li. Affordancellm: Grounding
affordance from vision language models. InProceedings of
the IEEE/CVF Conference on Computer Vision and Pattern
Recognition, pages 7587–7597, 2024. 4
[41] Delin Qu, Haoming Song, Qizhi Chen, Yuanqi Yao, Xinyi
Ye, Yan Ding, Zhigang Wang, JiaYuan Gu, Bin Zhao,
Dong Wang, et al. Spatialvla: Exploring spatial represen-
tations for visual-language-action model.arXiv preprint
arXiv:2501.15830, 2025. 1, 2, 5
[42] Hao Shi, Bin Xie, Yingfei Liu, Lin Sun, Fengrong Liu,
Tiancai Wang, Erjin Zhou, Haoqiang Fan, Xiangyu Zhang,
and Gao Huang. Memoryvla: Perceptual-cognitive memory
in vision-language-action models for robotic manipulation.
arXiv preprint arXiv:2508.19236, 2025. 5
[43] Mustafa Shukor, Dana Aubakirova, Francesco Capuano,
Pepijn Kooijmans, Steven Palma, Adil Zouitine, Michel Ar-
actingi, Caroline Pascal, Martino Russi, Andres Marafioti,
et al. Smolvla: A vision-language-action model for afford-
able and efficient robotics.arXiv preprint arXiv:2506.01844,
2025. 5
[44] Shuhan Tan, Kairan Dou, Yue Zhao, and Philipp
Kr¨ahenb¨uhl. Interactive post-training for vision-language-
action models.arXiv preprint arXiv:2505.17016, 2025. 6
[45] Stone Tao, Fanbo Xiang, Arth Shukla, Yuzhe Qin, Xander
Hinrichsen, Xiaodi Yuan, Chen Bao, Xinsong Lin, Yulin
Liu, Tse-kai Chan, et al. Maniskill3: Gpu parallelized
robotics simulation and rendering for generalizable embod-
ied ai.arXiv preprint arXiv:2410.00425, 2024. 7
[46] Gemini Team, Rohan Anil, Sebastian Borgeaud, Jean-
Baptiste Alayrac, Jiahui Yu, Radu Soricut, Johan Schalkwyk,
Andrew M Dai, Anja Hauth, Katie Millican, et al. Gemini: a
family of highly capable multimodal models.arXiv preprint
arXiv:2312.11805, 2023. 1
[47] Gemini Robotics Team, Saminda Abeyruwan, Joshua
Ainslie, Jean-Baptiste Alayrac, Montserrat Gonzalez Are-
nas, Travis Armstrong, Ashwin Balakrishna, Robert Baruch,
Maria Bauza, Michiel Blokzijl, et al. Gemini robotics:
Bringing ai into the physical world.arXiv preprint
arXiv:2503.20020, 2025. 2
10

[48] Octo Model Team, Dibya Ghosh, Homer Walke, Karl
Pertsch, Kevin Black, Oier Mees, Sudeep Dasari, Joey
Hejna, Tobias Kreiman, Charles Xu, et al. Octo:
An open-source generalist robot policy.arXiv preprint
arXiv:2405.12213, 2024. 1, 5
[49] Yuqi Wang, Xinghang Li, Wenxuan Wang, Junbo Zhang,
Yingyan Li, Yuntao Chen, Xinlong Wang, and Zhaoxi-
ang Zhang. Unified vision-language-action model.arXiv
preprint arXiv:2506.19850, 2025. 5
[50] Ziyang Yan, Wenzhen Dong, Yihua Shao, Yuhang Lu,
Haiyang Liu, Jingwen Liu, Haozhe Wang, Zhe Wang, Yan
Wang, Fabio Remondino, et al. Renderworld: World
model with self-supervised 3d label. In2025 IEEE Inter-
national Conference on Robotics and Automation (ICRA),
pages 6063–6070. IEEE, 2025. 1
[51] Yifan Yang, Zhixiang Duan, Tianshi Xie, Fuyu Cao, Pinxi
Shen, Peili Song, Piaopiao Jin, Guokang Sun, Shaoqing
Xu, Yangwei You, et al. Fpc-vla: A vision-language-action
framework with a supervisor for failure prediction and cor-
rection.arXiv preprint arXiv:2509.04018, 2025. 5
[52] Tianyuan Yuan, Yicheng Liu, Chenhao Lu, Zhuoguang
Chen, Tao Jiang, and Hang Zhao. Depthvla: Enhancing
vision-language-action models with depth-aware spatial rea-
soning.arXiv preprint arXiv:2510.13375, 2025. 2
[53] Michał Zawalski, William Chen, Karl Pertsch, Oier Mees,
Chelsea Finn, and Sergey Levine. Robotic control via
embodied chain-of-thought reasoning.arXiv preprint
arXiv:2407.08693, 2024. 1
[54] Xiaohua Zhai, Basil Mustafa, Alexander Kolesnikov, and
Lucas Beyer. Sigmoid loss for language image pre-training.
InProceedings of the IEEE/CVF international conference on
computer vision, pages 11975–11986, 2023. 5
[55] Jiahui Zhang, Yurui Chen, Yueming Xu, Ze Huang, Yan-
peng Zhou, Yu-Jie Yuan, Xinyue Cai, Guowei Huang,
Xingyue Quan, Hang Xu, et al. 4d-vla: Spatiotemporal
vision-language-action pretraining with cross-scene calibra-
tion.arXiv preprint arXiv:2506.22242, 2025. 2
[56] Jianke Zhang, Yanjiang Guo, Yucheng Hu, Xiaoyu Chen, Xi-
ang Zhu, and Jianyu Chen. Up-vla: A unified understanding
and prediction model for embodied agent.arXiv preprint
arXiv:2501.18867, 2025. 3
[57] Shiduo Zhang, Zhe Xu, Peiju Liu, Xiaopeng Yu, Yuan Li,
Qinghui Gao, Zhaoye Fei, Zhangyue Yin, Zuxuan Wu, Yu-
Gang Jiang, et al. Vlabench: A large-scale benchmark
for language-conditioned robotics manipulation with long-
horizon reasoning tasks. InProceedings of the IEEE/CVF
International Conference on Computer Vision, pages 11142–
11152, 2025. 2, 5, 6, 12
[58] Wenyao Zhang, Hongsi Liu, Zekun Qi, Yunnan Wang, Xin-
qiang Yu, Jiazhao Zhang, Runpei Dong, Jiawei He, Fan
Lu, He Wang, et al. Dreamvla: a vision-language-action
model dreamed with comprehensive world knowledge.arXiv
preprint arXiv:2507.04447, 2025. 1, 3, 5
[59] Zhengshen Zhang, Hao Li, Yalun Dai, Zhengbang Zhu, Lei
Zhou, Chenchen Liu, Dong Wang, Francis EH Tay, Sijin
Chen, Ziwei Liu, et al. From spatial to actions: Ground-
ing vision-language-action model in spatial foundation pri-
ors.arXiv preprint arXiv:2510.17439, 2025. 2
[60] Qingqing Zhao, Yao Lu, Moo Jin Kim, Zipeng Fu, Zhuoyang
Zhang, Yecheng Wu, Zhaoshuo Li, Qianli Ma, Song Han,
Chelsea Finn, et al. Cot-vla: Visual chain-of-thought rea-
soning for vision-language-action models. InProceedings
of the Computer Vision and Pattern Recognition Conference,
pages 1702–1713, 2025. 3, 5
[61] Tony Z Zhao, Vikash Kumar, Sergey Levine, and Chelsea
Finn. Learning fine-grained bimanual manipulation with
low-cost hardware.arXiv preprint arXiv:2304.13705, 2023.
1
[62] Haoyu Zhen, Xiaowen Qiu, Peihao Chen, Jincheng Yang,
Xin Yan, Yilun Du, Yining Hong, and Chuang Gan. 3d-vla:
A 3d vision-language-action generative world model.arXiv
preprint arXiv:2403.09631, 2024. 1
[63] Jinliang Zheng, Jianxiong Li, Dongxiu Liu, Yinan Zheng,
Zhihao Wang, Zhonghong Ou, Yu Liu, Jingjing Liu, Ya-
Qin Zhang, and Xianyuan Zhan. Universal actions for en-
hanced embodied foundation models. InProceedings of the
Computer Vision and Pattern Recognition Conference, pages
22508–22519, 2025. 5
[64] Ruijie Zheng, Yongyuan Liang, Shuaiyi Huang, Jianfeng
Gao, Hal Daum ´e III, Andrey Kolobov, Furong Huang, and
Jianwei Yang. Tracevla: Visual trace prompting enhances
spatial-temporal awareness for generalist robotic policies.
arXiv preprint arXiv:2412.10345, 2024. 5
[65] Wenzhao Zheng, Weiliang Chen, Yuanhui Huang, Borui
Zhang, Yueqi Duan, and Jiwen Lu. Occworld: Learning a 3d
occupancy world model for autonomous driving. InEuro-
pean conference on computer vision, pages 55–72. Springer,
2024. 1
[66] Chunting Zhou, Lili Yu, Arun Babu, Kushal Tirumala,
Michihiro Yasunaga, Leonid Shamis, Jacob Kahn, Xuezhe
Ma, Luke Zettlemoyer, and Omer Levy. Transfusion: Pre-
dict the next token and diffuse images with one multi-modal
model.arXiv preprint arXiv:2408.11039, 2024. 2
[67] Brianna Zitkovich, Tianhe Yu, Sichun Xu, Peng Xu, Ted
Xiao, Fei Xia, Jialin Wu, Paul Wohlhart, Stefan Welker,
Ayzaan Wahid, et al. Rt-2: Vision-language-action models
transfer web knowledge to robotic control. InConference on
Robot Learning, pages 2165–2183. PMLR, 2023. 2
11

A. Dataset Description
In this section, we present a comprehensive characterization
of the benchmark datasets and the custom-collected data
used for model training in our experiments. We system-
atically report key statistics, including the total number of
episodes, frame counts, and other relevant properties, which
is summarized in Table 7 below:
Type Dataset Embodiment DoF Episodes Frames FPS
Simulation
LIBERO Franka 7 1,693 273,465 10
LIBERO-PlusFranka 7 14,347 2,238,036 20
VLABench Franka 7 4,713 528,398 10
Real-World
Wipe StainAgiBot G1 22 177 356,316 30
Pour WaterAgiBot G1 22 1,821 5,062,506 30
Open-set PickAgiBot G1 22 1,936 219,824 30
Open-set PickAgileX 14 962 251,283 30
Table 7. Dataset statistics.
Simulation Benchmarks.We utilize three publicly re-
leased simulation datasets,i.e., LIBERO [32], LIBERO-
Plus [15], and VLABench [57]. Specifically, the LIBERO
dataset contains1,693episodes and273,465frames,
recorded at a fixed10Hz. Its demonstrations exhibit rel-
atively uniform trajectory lengths and smooth motion pat-
terns, making it widely adopted benchmark in community.
However, due to the increasing performance satura-
tion observed on LIBERO, LIBERO-Plus is recently intro-
duced to provide a more challenging and diversified eval-
uation setting. LIBERO-Plus provides14,347episodes
and2,238,036frames, captured at20Hz. In contrast to
the homogeneous trajectories in LIBERO, LIBERO-Plus
explicitly emphasizes a perturbation-oriented design. The
demonstrations display substantially larger variations in
motion magnitude and camera–robot viewpoint configura-
tion. These characteristics make it a more suitable bench-
mark for evaluating policy generalization under structured
distribution shifts.
Besides these two datasets, we further benchmark our
method on VLABench, whose training set includes4,713
episodes and528,398frames, recorded at10Hz, which re-
quires a higher level of visual and physical understanding
from the policy.
Real-World Experiment.For real-world deployment, we
collect demonstrations across3tasks,i.e., Wipe Stain, Pour
Water, and Open-set Pick, as shown in Table 7.
The “Wipe Stain” dataset contains177episodes with
356,316frames, characterized by dense tool–surface con-
tact and fine-grained force control. The “Pour Water”
dataset includes1,821episodes and5,062,506frames. Its
large scale stems from the task’s long-horizon and multi-
stage nature. Regarding the “Open-set Pick” task, the
AgiBot G1 subset provides1,936episodes with219,824
frames, while the AgileX subset offers962episodes with
251,283frames, both featuring diverse tabletop layouts and
natural-language instructions.
Task Action Space Action Horizon State Batch Size Training Step
LIBERO Delta EEF 10×128 40KLIBERO-PlusDelta EEF 10×128 100KVLABench Abs EEF 10✓128 60K
Wipe Stain Abs Joint 30✓128 50KPour Water Abs Joint 30✓128 240KOpen-set PickAbs Joint 30✓128 50KOpen-set Pick† Abs Joint 30✓128 50K
Table 8. Training details. Note that the “Open-set Pick †” task is
performed on AgileX platform.
B. Training & Evaluation Details
Training Details.We describe the task-specific training
configurations,e.g., action space and state usage, for bet-
ter understanding.
As presented in Table 8, for the LIBERO and LIBERO-
Plus suites, the policy is trained using delta end-effector
control (Delta EEF) with an action horizon of10steps. In
particular, no privileged state information is provided dur-
ing training. We utilize a global batch size of128and train
the policies for40K and100K steps, respectively. Similarly,
we train our models in VLABench for60K steps, while
adopting state input and absolute end-effector (Abs EEF)
actions to align the benchmark’s control convention.
In terms of the real-world tasks, we utilize Abs Joint con-
trol with a longer action horizon of30. Unlike the simula-
tor benchmarks, these tasks additionally provide structured
robot state observations to improve robustness under real-
world sensing and actuation noise. Our models are trained
for50K,240K, and50K steps, in “Wipe Stain”, “Pour Wa-
ter”, and “Open-set Pick” tasks, respectively, with same
batch size of128.
Evaluation Details.Next, we illustrate the evaluation pro-
tocols and success criteria for all real-world tasks. Each
task is assessed using fixed and repeatable initializations to
ensure reproducibility and reduce environmental variance.
Concretely, in terms of the “Wipe Stain” task, we pre-
define three initial sponge poses. For each pose, the robot
is required to clean stains placed at four distinct table loca-
tions. Every configuration is executed twice, resulting in24
trials in total. A trial is considered successful if the robot
grasps the sponge and removes the stain from the specified
location.
As for the “Pour Water”, we standardize six predefined
relative configurations between the bottle and the glass.
Then, each configuration is executed two times. A trial is
counted as successful if the robot lifts the bottle, pours wa-
ter into the cup, and places the bottle back onto the coaster.
Note that minor spillage of water when pouring is allowed.
Eventually, regarding the “Open-set Pick” task, we ini-
tialize ten object arrangements on the table, containing both
in-distribution and out-of-distribution instances. In each ar-
rangement, the robot is instructed to grasp a specified target
object using either its left or right arm, as indicated by the
12

Name EAR IAR Camera Robot Language Light Background Noise Layout Avg.
Baseline 70.3 41.7 81.1 97.394.671.8 84.9 75.7
#1 ✓ 88.763.580.4 94.0 90.289.584.2 83.7
#2 ✓ 80.7 48.782.6 97.790.9 84.386.0 80.4
#3 ✓ ✓ 91.262.5 80.3 95.1 91.5 88.3 84.9 84.1
Table 9. Module ablations on LIBERO-Plus benchmark. The performance is gradually improved with the addition of proposed methods.
Name Action Head EAR LIBERO LIBERO-Plus
Param. DenoiseParam. DenoiseSpatial Object Goal Long Avg.Camera Robot Language Light Background Noise Layout Avg.
Baseline300M 10 - - 98.6 99.0 96.4 92.2 96.6 70.3 41.7 81.1 97.3 94.671.8 84.9 75.7
#1 600M 10 - - 97.6 98.4 97.8 96.4 97.6 68.7 44.8 83.1 96.4 92.7 66.6 84.1 74.9
#2 600M 20 - - 97.8 98.8 98.0 95.2 97.5 70.0 44.8 82.797.693.1 66.7 83.2 75.1
#3 300M 5 300M 5 98.699.697.8 95.4 97.9 88.2 62.4 81.5 95.0 91.5 88.685.3 83.9
#4 300M 10 300M 10 99.0 99.4 98.0 96.6 98.3 88.7 63.580.4 94.0 90.289.584.2 83.7
#4 300M 10 300M 10 99.0 99.4 98.0 96.6 98.3 88.7 63.580.4 94.0 90.289.584.2 83.7
#5 300M 10 150M 10 99.299.2 97.8 94.2 97.6 86.4 54.3 81.7 92.2 91.4 89.1 82.1 81.7
#6 300M 10 250M 10 99.0 98.298.694.2 97.5 87.2 59.7 81.1 95.0 93.7 87.4 83.5 83.1
#7 300M 10 500M 10 98.4 99.4 96.6 94.2 97.0 80.8 57.684.195.6 92.1 79.8 83.7 80.9
Table 10. Effects of parameters and denoise steps on policy performance. The best results are highlighted inbold, and the second-best
results are underlined. Note that the IAR module is not added in this experiment.
instruction. Each arm–object pair is evaluated twice, result-
ing in40trials overall. A trial is deemed successful if the
robot grasps the instructed object with the correct arm.
Across all tasks, evaluations are carried out by trained
operators with substantial prior testing experience, and suc-
cess rates are computed as the proportion of successful trials
relative to the total number of executed attempts.
C. More Experimental Results
In this section, we provide additional quantitative experi-
ments to substantiate the effectiveness of our proposed ap-
proach and to empirically uncover several insightful phe-
nomena. Specifically, the experimental analyses comprise
three parts: (1) ablation study conducted on the LIBERO-
Plus benchmark in Table 9, (2) an investigation of how
the parameter sizes of the Action Head and Explicit Ac-
tion Reasoner (EAR), as well as the number of denoising
steps, influence policy performance in Table 10, and (3) a
comparative study examining the relationship among infer-
ence latency, model size, and performance in Table 11. Note
that we adoptπ 0.5 [22] as the baseline method, denoted as
“Baseline”.
Module Ablation.As shown in Table 9, incorporating
the proposed reasoning modules consistently improves pol-
icy performance on the LIBERO-Plus benchmark. Adding
the EAR module,i.e., experiment “#1”, yields a clear gain
over the baseline, increasing the average success rate from
75.7%to83.7%. This improvement can be attributed to
EAR’s ability to generate an explicit reference action tra-
jectory, which significantly reduces the ambiguity in map-
ping complex visual or linguistic observations to low-level
actions, such as camera shifts and background changes.
Meanwhile, incorporating only the IAR (“#2”) also im-
proves the performance from75.7%to80.4%, indicating
that decoding the latent action-related semantics within the
vision–language backbone provides useful behavioral pri-
ors. Finally, combining EAR and IAR (“#3”) achieves the
highest success rate of84.1%, demonstrating their comple-
mentary effects,i.e., EAR provides explicit motion guid-
ance, while IAR supplies dense representation-level priors.
Effect of Model Scaling & Denoising Budget.Then, we
analyze the superiority of our method by comparing settings
with matched total model parameters and denoising steps.
As shown in Table 10, firstly, we enlarge the model size of
the action head and increase the number of denoising steps
in experiments “#1” and “#2”, to construct fair baselines for
subsequent comparison. We observe a preliminary observa-
tion,i.e., increasing the model size or denoising steps does
not reliably enhance performance. Specifically, compared
with the baseline, while “#1” improves performance on the
LIBERO benchmark, it simultaneously drops on LIBERO-
Plus. Next, comparing “#1” and “#2” reveals that further in-
creasing denoising steps yields only negligible fluctuations.
Subsequently, we incorporate the EAR module under
fully matched overall parameterization and denoising bud-
gets. Concretely, in both comparison pairs, “#1” with “#3”
and “#2” with “#4”, we consistently observe notable perfor-
13

Name EAR IAR Param. LatencyLIBERO LIBERO-Plus
Avg. SR Avg. SR
Baseline 3.35B 91ms 96.9 75.7
#1 ✓ 3.80B 110ms 98.3 83.7
#2 ✓ 3.36B 93ms 98.1 80.4
#3 ✓ ✓ 3.81B 112ms 98.5 84.1
Table 11. Ablation experiment on model efficiency and perfor-
mance.
mance improvements on both benchmarks, once the EAR
module is introduced. This indicates that the performance
gains originate from our proposed action chain-of-thought.
The proposed mechanism supplies explicit reference ac-
tions that effectively mitigate the intrinsic instability of ac-
tion prediction, especially under challenging external per-
turbations, as shown in the LIBERO-Plus, enabling a more
reliable and grounded generalist robotic policy.
Effect of EAR Scale.Moreover, we investigate how var-
ious scale of the EAR module influences action prediction
fidelity. To isolate the effect of EAR, we keep the action
head parameters and the denoising schedule strictly fixed,
while scaling the EAR module to150M,250M,300M, and
500M parameters via adjusting hidden size. As presented
in Table 10, through the comparison across experiments
“#4”, “#5”, “#6”, and “#7”, we find that although all EAR-
equipped variants outperform non-EAR baselines on both
benchmarks, the performance trend is non-monotonic. Ap-
plying moderate EAR scales,e.g.,300M, yields the great-
est improvement. Particularly, as evidenced in “#7” in Ta-
ble 10, when the parameter of EAR module even exceeds
that of the action head, we observe a marked drop in per-
formance. We attribute this degradation to the tendency of
an over-parameterized EAR to overfit spurious correlations
during training. Therefore, it generates reference action tra-
jectories that are systematically biased, which ultimately
misdirect the action head toward suboptimal predictions.
Latency Analysis.In Table 11, we further examine the in-
ference efficiency of our approach in terms of both param-
eter count and end-to-end latency. As additional reasoning
modules are introduced, we observe a slight increase in la-
tency. Incorporating the EAR module raises latency from
91ms to110ms, while adding the IAR module introduces
only an additional2ms. However, this marginal overhead is
outweighed by the substantial improvement, which reflects
a favorable trade-off.
D. Limitations & Future Works
In this section, we discuss the limitations existing in our
work and promising directions for future research.
Although our proposed action chain-of-thought (ACoT)
substantially boosts policy performance, our framework
still exhibits several constraints. The reasoning modules
introduce additional computational cost, which, while rela-
tively modest compared to the performance gains, may pose
challenges for deployment on resource-constrained robotic
platforms. Besides, another limitation stems from the fact
that the prevailing action representation in the community
is implemented as action chunks,i.e., sequences of low-
level control commands such as joint angles or end-effector
poses. While such representations faithfully encode the
executed motions, they lack explicit geometric structure
that would facilitate higher-level spatial reasoning, such as
object-centric coordination and contact geometry. Hence,
the potential of ACoT reasoning may not be fully unleashed.
Enriching action representations with spatially grounded in-
formation to enable ACoT to operate in geometrically inter-
pretable 3D space, constitutes an interesting and promising
avenue for future exploration.
E. LLM Usage Statement
In this paper, we employ Large Language Models (LLMs)
solely for minor linguistic refinement during the manuscript
preparation stage, such as correcting grammatical errors.
None of the technical content, implementation details, or
experimental results were generated by LLMs.
14

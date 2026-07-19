TOPIC_KEYWORDS: dict[str, list[str]] = {
    "LLM": [
        "llm",
        "large language model",
        "language model",
        "gpt",
        "transformer",
        "instruction tuning",
        "prompt engineering",
        "reasoning model",
        "chatbot",
        "tokenization",
        "natural language processing",
        "nlp",
        "generative ai",
        "text generation",
        "few-shot learning",
        "fine-tuning",
    ],
    "Agents": [
        "agent",
        "multi-agent systems",
        "tool use",
        "autonomous agents",
        "agentic workflow",
        "react framework",
        "planning algorithms",
        "decision making",
        "embodied agents",
        "ai assistants",
        "agent orchestration",
        "task decomposition",
    ],
    "Edge AI": [
        "edge ai",
        "edge computing",
        "tinyml",
        "on-device ai",
        "mobile ai",
        "embedded systems",
        "model quantization",
        "efficient inference",
        "spiking neural networks",
        "lnn",
        "knowledge distillation",
        "resource-constrained ai",
        "federated learning",
    ],
    "Robotics": [
        "robotics",
        "robot manipulation",
        "robot navigation",
        "robot locomotion",
        "embodied ai",
        "simulated to real transfer",
        "bimanual control",
        "robot learning",
        "reinforcement learning for robotics",
        "human-robot interaction",
        "autonomous driving",
    ],
    "Computer Vision": [
        "computer vision",
        "image recognition",
        "object detection",
        "image segmentation",
        "generative vision",
        "diffusion models",
        "neura rendering",
        "3d vision",
        "video analysis",
    ],
    "Reinforcement Learning": [
        "reinforcement learning",
        "rl",
        "deep reinforcement learning",
        "policy gradients",
        "q-learning",
        "multi-agent rl",
        "game theory",
        "optimal control",
    ],
}


def classify_topics(title: str, snippet: str | None) -> list[str]:
    text = f"{title} {(snippet or '')}".lower()
    matched: list[str] = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            matched.append(topic)
    if not matched:
        matched.append("General AI")
    return matched


def relevance_score(topics: list[str]) -> float:
    # Adjust scoring based on new topics if necessary
    priority = {"LLM", "Agents", "Edge AI", "Robotics", "Computer Vision", "Reinforcement Learning"}
    hits = len(set(topics) & priority)
    if hits == 0:
        return 0.35
    # Scaled score: higher priority topics give a higher score
    return min(1.0, 0.55 + hits * 0.10)

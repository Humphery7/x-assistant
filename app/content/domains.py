"""The engineering world the assistant writes about.

A domain is a broad field (software, hardware, robotics...). Each domain owns
the disciplines a post can be tagged with and a bank of concrete, narrow topic
seeds. Seeds are deliberately specific: "why retries without jitter make
outages worse" produces better writing than "resilience".
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Domain:
    key: str
    name: str
    blurb: str
    disciplines: tuple[str, ...]
    topics: tuple[str, ...]
    search_terms: tuple[str, ...]


DOMAINS: dict[str, Domain] = {
    "software": Domain(
        key="software",
        name="Software & AI",
        blurb="Distributed systems, backend, developer tools, machine learning.",
        disciplines=("Software engineering", "AI and machine learning"),
        topics=(
            "Why retries without jitter make outages worse",
            "The hidden cost of an ORM once the schema stops being simple",
            "What fine-tuning actually changes versus a good prompt",
            "Idempotency keys are a product decision, not a database trick",
            "Feature flags are technical debt with a nice UI",
            "Why your vector database is probably just Postgres",
            "The N+1 query that only shows up under production traffic",
            "Designing APIs that fail loudly instead of silently",
            "What RAG gets wrong about retrieval",
            "Why distributed transactions are rare in real systems",
            "How SLOs quietly change what you decide to build",
            "Evals are the tests of the AI era",
            "Cold starts are an architecture smell",
            "Most AI agents are workflows with extra steps",
            "Boring queues beat clever event buses",
            "The migration you can roll back is worth more than the faster one",
        ),
        search_terms=("backend engineering", "distributed systems", "LLM engineering", "developer tools"),
    ),
    "hardware": Domain(
        key="hardware",
        name="Hardware & Electronics",
        blurb="Semiconductors, PCB design, power, analog and electrical engineering.",
        disciplines=("Semiconductors", "Electronics", "Electrical engineering", "Energy systems"),
        topics=(
            "Why chiplets trade yield for flexibility",
            "The thermal wall that shaped modern CPUs",
            "Decoupling capacitors are the part everyone forgets",
            "Why 3nm is a marketing number, not a gate length",
            "Power delivery is the hardest part of a fast board",
            "What electromigration does to a chip over ten years",
            "The analog world does not care about your abstraction layer",
            "Why MOSFETs are still winning",
            "Clock distribution is the quiet engineering problem",
            "Silicon bring-up is ninety percent measurement",
            "The real cost of a respin",
            "Your oscilloscope probe changes the circuit you measure",
            "HBM bandwidth is not free",
            "Board-level EMI is a layout problem, not a filter problem",
            "Why battery management is mostly estimation",
        ),
        search_terms=("semiconductor", "PCB design", "power electronics", "electrical engineering"),
    ),
    "robotics": Domain(
        key="robotics",
        name="Robotics & Control",
        blurb="Robotics, embedded systems, firmware and control engineering.",
        disciplines=("Robotics", "Embedded systems", "Control engineering"),
        topics=(
            "Why PID still beats fancy controllers in production",
            "Jitter is the enemy of every control loop",
            "The difference between a demo robot and a product",
            "Why your IMU drifts and what to do about it",
            "Determinism matters more than raw clock speed",
            "Sensor fusion is mostly knowing when to distrust a sensor",
            "The actuator is usually the bottleneck",
            "ROS is great for research and painful for shipping",
            "Watchdog timers are the least glamorous safety feature",
            "How encoder resolution changes your control design",
            "Compliance is a feature, not a bug",
            "Field robots fail on the mundane things",
            "Sim-to-real transfer still surprises people",
            "The wiring harness is the real architecture",
            "Why interrupt latency ruins your loop timing",
        ),
        search_terms=("robotics engineering", "embedded systems", "control systems", "firmware"),
    ),
    "mechanical": Domain(
        key="mechanical",
        name="Mechanical & Motorsport",
        blurb="Mechanical design, automotive engineering and Formula 1.",
        disciplines=("Mechanical design", "Automotive engineering", "Formula 1"),
        topics=(
            "Why F1 teams obsess over a millimetre of ride height",
            "Bump stops do more than limit travel",
            "Tolerance stack-up is where good designs die",
            "Why ground effect came back",
            "The brake bias decision that wins races",
            "Thermal management is a packaging problem, not a cooling problem",
            "Carbon fibre is a design constraint, not a material upgrade",
            "Fasteners are a reliability system",
            "The aero-mechanical conflict nobody talks about",
            "A simulation is only as good as its tyre model",
            "Why production cars use suspension geometry F1 abandoned",
            "Fatigue life is a design input, not a QA step",
            "Weight is a budget you spend, not a number you minimise",
            "Wind tunnel correlation is the real engineering problem",
            "Why serviceability is designed in, not added later",
        ),
        search_terms=("mechanical engineering", "automotive engineering", "Formula 1 engineering", "vehicle dynamics"),
    ),
    "aerospace": Domain(
        key="aerospace",
        name="Aerospace & Systems",
        blurb="Aerospace, systems engineering, safety and certification.",
        disciplines=("Aerospace engineering", "Systems engineering", "Safety engineering"),
        topics=(
            "Why margins exist in structural design",
            "Redundancy is expensive until it is not",
            "The certification process is part of the design",
            "Pressurisation cycles limit an airframe's life",
            "Why flight software is written so conservatively",
            "Failure modes you cannot test for",
            "What a factor of safety actually buys you",
            "Thermal expansion is a constant companion in design",
            "Weight and cost trade against each other differently in orbit",
            "The difference between reliability and availability",
            "Why redundancy sometimes makes a system less safe",
            "Requirements are a model, and models can be wrong",
        ),
        search_terms=("aerospace engineering", "systems engineering", "flight software", "safety engineering"),
    ),
    "civil_biomed": Domain(
        key="civil_biomed",
        name="Civil, Biomedical & Materials",
        blurb="Structures, infrastructure, medical devices and materials.",
        disciplines=("Civil engineering", "Biomedical engineering", "Materials engineering"),
        topics=(
            "Concrete is a chemistry problem wearing a hard hat",
            "Why bridges are designed for loads they will never see",
            "Biocompatibility is a materials problem first",
            "The difference between a prototype and an implant",
            "Fatigue is the failure mode that hides",
            "Why drainage decides whether a structure survives",
            "Sterilisation constrains the design more than the biology does",
            "Creep is slow, and that is exactly the problem",
            "Structural monitoring is mostly deciding what not to measure",
            "Why medical device software is validated, not just tested",
            "Corrosion is a maintenance schedule, not an event",
            "Designing for disassembly is a materials decision",
        ),
        search_terms=("civil engineering", "biomedical engineering", "materials engineering", "structural engineering"),
    ),
}

FORMAT_LABELS: dict[str, str] = {
    "short_insight": "Short insight",
    "field_note": "Field note",
    "tradeoff": "Trade-off",
    "teardown": "Teardown",
    "question": "Question",
    "opinion": "Opinion",
    "explainer": "Explainer",
    "thread": "Thread",
}

# Formats that suit every discipline. Threads are added separately by the planner.
BASE_FORMATS: tuple[str, ...] = (
    "short_insight",
    "field_note",
    "tradeoff",
    "teardown",
    "question",
    "opinion",
    "explainer",
)


def all_domains() -> list[Domain]:
    return list(DOMAINS.values())


def domain_for(key: str | None) -> Domain:
    return DOMAINS.get(key or "", DOMAINS["software"])


def label_for_format(key: str) -> str:
    return FORMAT_LABELS.get(key, key.replace("_", " ").title())


def domain_keys() -> list[str]:
    return list(DOMAINS.keys())

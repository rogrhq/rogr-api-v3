from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, JSON, Text, ForeignKey, TIMESTAMP, Float
import uuid, datetime

class Base(DeclarativeBase):
    pass

def uuid_pk(): return str(uuid.uuid4())
def now(): return datetime.datetime.utcnow()

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_pk)
    email: Mapped[str] = mapped_column(String, unique=True)
    handle: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, default=now)
    auth_provider: Mapped[str | None] = mapped_column(String, nullable=True)

class Follow(Base):
    __tablename__ = "follows"
    follower_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), primary_key=True)
    followee_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, default=now)

class Analysis(Base):
    __tablename__ = "analyses"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_pk)
    user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"))
    input_type: Mapped[str] = mapped_column(String)  # text|url
    original_uri: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, default=now)
    status: Mapped[str] = mapped_column(String, default="queued")
    total_grade_numeric: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_label: Mapped[str | None] = mapped_column(String, nullable=True)
    summary_capsule_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ifcn_methodology_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

class MediaAsset(Base):
    __tablename__ = "media_assets"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_pk)
    analysis_id: Mapped[str] = mapped_column(String, ForeignKey("analyses.id"))
    kind: Mapped[str] = mapped_column(String)  # text|image|audio|video
    storage_uri: Mapped[str] = mapped_column(String)
    checksum: Mapped[str] = mapped_column(String)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(String, nullable=True)

class Claim(Base):
    __tablename__ = "claims"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_pk)
    analysis_id: Mapped[str] = mapped_column(String, ForeignKey("analyses.id"))
    text: Mapped[str] = mapped_column(Text)
    tier: Mapped[str] = mapped_column(String)  # primary|secondary|tertiary
    priority: Mapped[int] = mapped_column(Integer, default=0)
    entities_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    scope_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

class SearchPlan(Base):
    __tablename__ = "search_plans"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_pk)
    claim_id: Mapped[str] = mapped_column(String, ForeignKey("claims.id"))
    provider: Mapped[str] = mapped_column(String)
    arm: Mapped[str] = mapped_column(String)  # 'A'|'B'
    seed: Mapped[str] = mapped_column(String)
    queries_json: Mapped[dict] = mapped_column(JSON)
    date_window: Mapped[str | None] = mapped_column(String, nullable=True)
    constraints_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, default=now)

class Source(Base):
    __tablename__ = "sources"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_pk)
    claim_id: Mapped[str] = mapped_column(String, ForeignKey("claims.id"))
    arm: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    publisher: Mapped[str] = mapped_column(String)
    published_at: Mapped[str | None] = mapped_column(String, nullable=True)
    snapshot_uri: Mapped[str] = mapped_column(String)
    snippet: Mapped[str] = mapped_column(Text)
    dedupe_key: Mapped[str] = mapped_column(String)

class Evidence(Base):
    __tablename__ = "evidence"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_pk)
    claim_id: Mapped[str] = mapped_column(String, ForeignKey("claims.id"))
    arm: Mapped[str] = mapped_column(String)
    source_id: Mapped[str] = mapped_column(String, ForeignKey("sources.id"))
    relevance_score: Mapped[int] = mapped_column(Integer)
    stance: Mapped[str] = mapped_column(String)  # support|refute|neutral
    quality_letter: Mapped[str] = mapped_column(String)  # A..F
    features_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

class ConsensusRun(Base):
    __tablename__ = "consensus_runs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_pk)
    claim_id: Mapped[str] = mapped_column(String, ForeignKey("claims.id"))
    seeds_json: Mapped[dict] = mapped_column(JSON)
    overlap_ratio: Mapped[float] = mapped_column(Float)
    conflict_score: Mapped[float] = mapped_column(Float)
    stability: Mapped[float] = mapped_column(Float)

class Verdict(Base):
    __tablename__ = "verdicts"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_pk)
    claim_id: Mapped[str] = mapped_column(String, ForeignKey("claims.id"))
    claim_grade_numeric: Mapped[int] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(String)
    rationale: Mapped[str] = mapped_column(Text)

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_pk)
    analysis_id: Mapped[str] = mapped_column(String, ForeignKey("analyses.id"))
    actor: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String)
    metadata_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, default=now)

class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_pk)
    name: Mapped[str] = mapped_column(String)
    kind: Mapped[str] = mapped_column(String)

class AnalysisTag(Base):
    __tablename__ = "analysis_tags"
    analysis_id: Mapped[str] = mapped_column(String, ForeignKey("analyses.id"), primary_key=True)
    tag_id: Mapped[str] = mapped_column(String, ForeignKey("tags.id"), primary_key=True)

class Entity(Base):
    __tablename__ = "entities"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_pk)
    name: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    canonical_id: Mapped[str | None] = mapped_column(String, nullable=True)

class ClaimEntity(Base):
    __tablename__ = "claim_entities"
    claim_id: Mapped[str] = mapped_column(String, ForeignKey("claims.id"), primary_key=True)
    entity_id: Mapped[str] = mapped_column(String, ForeignKey("entities.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String)

class FeedPost(Base):
    __tablename__ = "feed_posts"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_pk)
    analysis_id: Mapped[str] = mapped_column(String, ForeignKey("analyses.id"))
    author_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    visibility: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, default=now)

class Like(Base):
    __tablename__ = "likes"
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), primary_key=True)
    post_id: Mapped[str] = mapped_column(String, ForeignKey("feed_posts.id"), primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, default=now)

class Save(Base):
    __tablename__ = "saves"
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), primary_key=True)
    analysis_id: Mapped[str] = mapped_column(String, ForeignKey("analyses.id"), primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, default=now)

class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_pk)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    kind: Mapped[str] = mapped_column(String)  # "follow" | "job_completed" | "job_failed" | ...
    payload_json: Mapped[dict] = mapped_column(JSON)
    dedupe_key: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, default=now)
    read_at: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP, nullable=True)
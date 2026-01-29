from sqlalchemy import create_engine, Column, String, Integer, DateTime, JSON, Text, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import os
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///controller.db")

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

class Agent(Base):
    __tablename__ = "agents"
    id = Column(String, primary_key=True)
    name = Column(String)
    platform = Column(String)
    ip = Column(String)
    last_seen = Column(DateTime)
    capabilities = Column(JSON)
    metadata_json = Column('metadata', JSON)

class CommandHistory(Base):
    __tablename__ = "command_history"
    id = Column(Integer, primary_key=True)
    agent_id = Column(String, index=True)
    command = Column(Text)
    output = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean)

class ActivityLog(Base):
    __tablename__ = "activity_log"
    id = Column(Integer, primary_key=True)
    agent_id = Column(String, index=True, nullable=True)
    activity_type = Column(String)
    details = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

class AgentGroup(Base):
    __tablename__ = "agent_groups"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(Text)
    tags = Column(JSON)
    members = relationship("AgentGroupMembership", back_populates="group")

class AgentGroupMembership(Base):
    __tablename__ = "agent_group_membership"
    agent_id = Column(String, primary_key=True)
    group_id = Column(Integer, ForeignKey("agent_groups.id"), primary_key=True)
    group = relationship("AgentGroup", back_populates="members")

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=True)
    action = Column(String)
    agent_id = Column(String, nullable=True)
    details = Column(Text)
    severity = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String, nullable=True)

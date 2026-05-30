"""
Database models and connection management for the Drug Discovery AI Agent.
Uses SQLAlchemy for ORM and database operations.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.pool import QueuePool
from config import get_config

Base = declarative_base()

class UserSession(Base):
    """User session tracking"""
    __tablename__ = 'user_sessions'

    id = Column(String(50), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    user_agent = Column(String(500))
    ip_address = Column(String(45))
    session_metadata = Column(JSON)

    # Relationships
    chat_messages = relationship("ChatMessage", back_populates="session")
    search_queries = relationship("SearchQuery", back_populates="session")

class ChatMessage(Base):
    """Chat message history"""
    __tablename__ = 'chat_messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), ForeignKey('user_sessions.id'))
    message = Column(Text, nullable=False)
    response = Column(Text)
    agent_type = Column(String(50), default='default')
    created_at = Column(DateTime, default=datetime.utcnow)
    processing_time = Column(Float)
    message_metadata = Column(JSON)

    # Relationships
    session = relationship("UserSession", back_populates="chat_messages")
    actions = relationship("AgentAction", back_populates="chat_message")

class AgentAction(Base):
    """Agent actions taken during chat"""
    __tablename__ = 'agent_actions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_message_id = Column(Integer, ForeignKey('chat_messages.id'))
    tool_name = Column(String(100), nullable=False)
    tool_input = Column(Text)
    tool_output = Column(Text)
    success = Column(Boolean, default=True)
    execution_time = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    chat_message = relationship("ChatMessage", back_populates="actions")

class SearchQuery(Base):
    """Search query history"""
    __tablename__ = 'search_queries'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), ForeignKey('user_sessions.id'))
    query_type = Column(String(50), nullable=False)  # 'rag', 'compounds', 'papers', etc.
    query = Column(Text, nullable=False)
    results_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    processing_time = Column(Float)
    search_metadata = Column(JSON)

    # Relationships
    session = relationship("UserSession", back_populates="search_queries")

class CachedResult(Base):
    """Cached API results"""
    __tablename__ = 'cached_results'

    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(200), unique=True, nullable=False)
    result_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    hit_count = Column(Integer, default=0)
    source = Column(String(100))  # 'pubmed', 'pdb', 'pubchem', etc.

class ToolUsageStats(Base):
    """Tool usage statistics"""
    __tablename__ = 'tool_usage_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tool_name = Column(String(100), nullable=False)
    call_count = Column(Integer, default=0)
    total_execution_time = Column(Float, default=0.0)
    avg_execution_time = Column(Float, default=0.0)
    last_called = Column(DateTime)
    error_count = Column(Integer, default=0)
    success_rate = Column(Float, default=1.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SystemLog(Base):
    """System logging"""
    __tablename__ = 'system_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    module = Column(String(100))
    function = Column(String(100))
    user_id = Column(String(50))
    session_id = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    log_metadata = Column(JSON)

class DatabaseManager:
    """Database connection and session management"""

    def __init__(self):
        self.config = get_config()
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()

    def _initialize_database(self):
        """Initialize database connection"""
        try:
            database_url = self.config.database.url
            if database_url == "sqlite:///drug_discovery.db":
                database_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "drug_discovery.db"))
                database_url = f"sqlite:///{database_path}"

            connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}

            self.engine = create_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=self.config.database.pool_size,
                max_overflow=self.config.database.max_overflow,
                pool_timeout=self.config.database.pool_timeout,
                connect_args=connect_args,
                echo=self.config.flask.debug
            )

            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )

            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            print("✓ Database initialized successfully")

        except Exception as e:
            print(f"✗ Database initialization failed: {e}")
            raise

    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()

    def close_session(self, session: Session):
        """Close a database session"""
        session.close()

    def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            from sqlalchemy import text
            session = self.get_session()
            session.execute(text("SELECT 1"))
            self.close_session(session)
            return True
        except Exception as e:
            print(f"Database health check failed: {e}")
            return False

# Global database manager instance
db_manager = DatabaseManager()

def get_db() -> Session:
    """Dependency for getting database session"""
    session = db_manager.get_session()
    try:
        yield session
    finally:
        db_manager.close_session(session)

def get_db_session() -> Session:
    """Get database session for manual management"""
    return db_manager.get_session()

def create_user_session(session_id: str, user_agent: str = None, ip_address: str = None) -> UserSession:
    """Create a new user session"""
    session = get_db_session()
    try:
        user_session = UserSession(
            id=session_id,
            user_agent=user_agent,
            ip_address=ip_address
        )
        session.add(user_session)
        session.commit()
        session.refresh(user_session)
        return user_session
    finally:
        session.close()

def log_chat_message(session_id: str, message: str, response: str = None,
                    agent_type: str = 'default', processing_time: float = None) -> ChatMessage:
    """Log a chat message"""
    session = get_db_session()
    try:
        chat_message = ChatMessage(
            session_id=session_id,
            message=message,
            response=response,
            agent_type=agent_type,
            processing_time=processing_time
        )
        session.add(chat_message)
        session.commit()
        session.refresh(chat_message)
        return chat_message
    finally:
        session.close()

def update_tool_stats(tool_name: str, execution_time: float, success: bool = True):
    """Update tool usage statistics"""
    session = get_db_session()
    try:
        # Get or create tool stats
        tool_stat = session.query(ToolUsageStats).filter_by(tool_name=tool_name).first()
        if not tool_stat:
            tool_stat = ToolUsageStats(tool_name=tool_name)
            session.add(tool_stat)

        # Update statistics
        tool_stat.call_count += 1
        tool_stat.total_execution_time += execution_time
        tool_stat.avg_execution_time = tool_stat.total_execution_time / tool_stat.call_count
        tool_stat.last_called = datetime.utcnow()

        if not success:
            tool_stat.error_count += 1

        tool_stat.success_rate = (tool_stat.call_count - tool_stat.error_count) / tool_stat.call_count

        session.commit()
    finally:
        session.close()

def get_tool_stats() -> Dict[str, Dict[str, Any]]:
    """Get tool usage statistics"""
    session = get_db_session()
    try:
        stats = session.query(ToolUsageStats).all()
        return {
            stat.tool_name: {
                'status': 'active',
                'callCount': stat.call_count,
                'avgLatency': f"{stat.avg_execution_time:.1f}ms",
                'lastCalled': stat.last_called.strftime("%H:%M %p") if stat.last_called else "Never",
                'successRate': f"{stat.success_rate:.1%}"
            }
            for stat in stats
        }
    finally:
        session.close()

def log_system_event(level: str, message: str, module: str = None,
                    function: str = None, user_id: str = None, session_id: str = None):
    """Log a system event"""
    session = get_db_session()
    try:
        log_entry = SystemLog(
            level=level,
            message=message,
            module=module,
            function=function,
            user_id=user_id,
            session_id=session_id
        )
        session.add(log_entry)
        session.commit()
    finally:
        session.close()

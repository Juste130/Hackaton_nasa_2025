"""
NASA Bioscience Publications Database Client
Client asynchrone pour opérations CRUD avec PostgreSQL et SQLAlchemy
"""

import asyncio
import uuid
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from sqlalchemy import Column, String, Text, Date, DateTime, Integer, Float, Boolean, ForeignKey, Table, ARRAY
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy.sql import text
from sqlalchemy import select, insert, update, delete
from pgvector.sqlalchemy import Vector
import logging
import os
from dotenv import load_dotenv

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger variables d'environnement
load_dotenv()

class Base(DeclarativeBase):
    pass

# Modèles SQLAlchemy
class Publication(Base):
    __tablename__ = 'publications'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pmcid: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    pmid: Mapped[Optional[str]] = mapped_column(String(20))
    doi: Mapped[Optional[str]] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract: Mapped[Optional[str]] = mapped_column(Text)
    publication_date: Mapped[Optional[date]] = mapped_column(Date)
    journal: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(768))
    
    # Relations
    authors = relationship("PublicationAuthor", back_populates="publication", cascade="all, delete-orphan")
    keywords = relationship("PublicationKeyword", back_populates="publication", cascade="all, delete-orphan")
    mesh_terms = relationship("PublicationMeshTerm", back_populates="publication", cascade="all, delete-orphan")
    text_sections = relationship("TextSection", back_populates="publication", cascade="all, delete-orphan")
    entities = relationship("PublicationEntity", back_populates="publication", cascade="all, delete-orphan")

class Author(Base):
    __tablename__ = 'authors'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firstname: Mapped[Optional[str]] = mapped_column(String(255))
    lastname: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    orcid: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class PublicationAuthor(Base):
    __tablename__ = 'publication_authors'
    
    publication_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('publications.id'), primary_key=True)
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('authors.id'), primary_key=True)
    author_order: Mapped[int] = mapped_column(Integer, nullable=False)
    affiliation: Mapped[Optional[str]] = mapped_column(Text)
    
    publication = relationship("Publication", back_populates="authors")
    author = relationship("Author")

class Keyword(Base):
    __tablename__ = 'keywords'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keyword: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100))

class PublicationKeyword(Base):
    __tablename__ = 'publication_keywords'
    
    publication_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('publications.id'), primary_key=True)
    keyword_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('keywords.id'), primary_key=True)
    
    publication = relationship("Publication", back_populates="keywords")
    keyword = relationship("Keyword")

class MeshTerm(Base):
    __tablename__ = 'mesh_terms'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    term: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    tree_number: Mapped[Optional[str]] = mapped_column(String(50))

class PublicationMeshTerm(Base):
    __tablename__ = 'publication_mesh_terms'
    
    publication_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('publications.id'), primary_key=True)
    mesh_term_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('mesh_terms.id'), primary_key=True)
    is_major_topic: Mapped[bool] = mapped_column(Boolean, default=False)
    
    publication = relationship("Publication", back_populates="mesh_terms")
    mesh_term = relationship("MeshTerm")

class TextSection(Base):
    __tablename__ = 'text_sections'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    publication_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('publications.id'))
    section_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    section_order: Mapped[Optional[int]] = mapped_column(Integer)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(768))
    
    publication = relationship("Publication", back_populates="text_sections")

class Entity(Base):
    __tablename__ = 'entities'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)

class PublicationEntity(Base):
    __tablename__ = 'publication_entities'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    publication_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('publications.id'))
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('entities.id'))
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    context: Mapped[Optional[str]] = mapped_column(Text)
    
    publication = relationship("Publication", back_populates="entities")
    entity = relationship("Entity")


class DatabaseClient:
    """Client asynchrone pour base de données NASA Bioscience Publications"""
    
    def __init__(self, database_url: Optional[str] = None):
        if database_url is None:
            database_url = os.getenv('POSTGRES_URL')
            if not database_url:
                raise ValueError("POSTGRES_URL non trouvée dans les variables d'environnement")
        
        # Convertir en URL async
        if database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
        elif not database_url.startswith('postgresql+asyncpg://'):
            database_url = f"postgresql+asyncpg://{database_url}"
        
        self.engine = create_async_engine(
            database_url,
            echo=False,  # Mettre True pour debug SQL
            pool_size=10,
            max_overflow=20
        )
        
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def create_tables(self):
        """Créer toutes les tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Tables créées avec succès")
    
    async def close(self):
        """Fermer la connexion"""
        await self.engine.dispose()
    
    # === CRUD Publications ===
    
    async def create_publication(self, publication_data: Dict[str, Any]) -> uuid.UUID:
        """Créer une publication avec toutes ses relations"""
        async with self.async_session() as session:
            try:
                # 1. Créer la publication principale
                pub = Publication(
                    pmcid=publication_data['pmcid'],
                    pmid=publication_data.get('pmid'),
                    doi=publication_data.get('doi'),
                    title=publication_data['title'],
                    abstract=publication_data.get('abstract'),
                    publication_date=self._parse_date(publication_data.get('publication_date')),
                    journal=publication_data.get('journal')
                )
                session.add(pub)
                await session.flush()  # Pour obtenir l'ID
                
                # 2. Traiter les auteurs
                if 'authors' in publication_data:
                    await self._add_authors_to_publication(session, pub.id, publication_data['authors'])
                
                # 3. Traiter les mots-clés
                if 'keywords' in publication_data:
                    await self._add_keywords_to_publication(session, pub.id, publication_data['keywords'])
                
                # 4. Traiter les MeSH terms
                if 'mesh_terms' in publication_data:
                    await self._add_mesh_terms_to_publication(session, pub.id, publication_data['mesh_terms'])
                
                # 5. Traiter les sections de texte
                if 'full_text_sections' in publication_data:
                    await self._add_text_sections_to_publication(session, pub.id, publication_data['full_text_sections'])
                
                await session.commit()
                logger.info(f"Publication {pub.pmcid} créée avec ID {pub.id}")
                return pub.id
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Erreur création publication {publication_data.get('pmcid', 'unknown')}: {e}")
                raise
    
    async def get_publication_by_pmcid(self, pmcid: str) -> Optional[Dict]:
        """Récupérer une publication par PMCID"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Publication).where(Publication.pmcid == pmcid)
            )
            publication = result.scalar_one_or_none()
            
            if publication:
                return await self._publication_to_dict(session, publication)
            return None
    
    async def get_publication_by_id(self, pub_id: uuid.UUID) -> Optional[Dict]:
        """Récupérer une publication par ID"""
        async with self.async_session() as session:
            result = await session.execute(
                select(Publication).where(Publication.id == pub_id)
            )
            publication = result.scalar_one_or_none()
            
            if publication:
                return await self._publication_to_dict(session, publication)
            return None
    
    async def search_publications(
        self, 
        query: Optional[str] = None,
        author: Optional[str] = None,
        journal: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Recherche de publications avec filtres"""
        async with self.async_session() as session:
            query_stmt = select(Publication)
            
            # Filtres
            if query:
                # Recherche full-text dans titre et abstract
                query_stmt = query_stmt.where(
                    text("title_search @@ plainto_tsquery(:query) OR abstract_search @@ plainto_tsquery(:query)")
                ).params(query=query)
            
            if author:
                # Recherche par nom d'auteur
                query_stmt = query_stmt.join(PublicationAuthor).join(Author).where(
                    Author.lastname.ilike(f"%{author}%")
                )
            
            if journal:
                query_stmt = query_stmt.where(Publication.journal.ilike(f"%{journal}%"))
            
            if date_from:
                query_stmt = query_stmt.where(Publication.publication_date >= date_from)
            
            if date_to:
                query_stmt = query_stmt.where(Publication.publication_date <= date_to)
            
            query_stmt = query_stmt.limit(limit)
            
            result = await session.execute(query_stmt)
            publications = result.scalars().all()
            
            return [await self._publication_to_dict(session, pub) for pub in publications]
    
    async def update_publication(self, pub_id: uuid.UUID, update_data: Dict[str, Any]) -> bool:
        """Mettre à jour une publication"""
        async with self.async_session() as session:
            try:
                result = await session.execute(
                    update(Publication)
                    .where(Publication.id == pub_id)
                    .values(**update_data, updated_at=datetime.utcnow())
                )
                await session.commit()
                return result.rowcount > 0
            except Exception as e:
                await session.rollback()
                logger.error(f"Erreur mise à jour publication {pub_id}: {e}")
                return False
    
    async def delete_publication(self, pub_id: uuid.UUID) -> bool:
        """Supprimer une publication"""
        async with self.async_session() as session:
            try:
                result = await session.execute(
                    delete(Publication).where(Publication.id == pub_id)
                )
                await session.commit()
                return result.rowcount > 0
            except Exception as e:
                await session.rollback()
                logger.error(f"Erreur suppression publication {pub_id}: {e}")
                return False
    
    # === Méthodes auxiliaires ===
    
    async def _add_authors_to_publication(self, session: AsyncSession, pub_id: uuid.UUID, authors_data: List[Dict]):
        """Ajouter des auteurs à une publication"""
        for i, author_data in enumerate(authors_data):
            # Vérifier si l'auteur existe
            result = await session.execute(
                select(Author).where(
                    Author.firstname == author_data.get('firstname'),
                    Author.lastname == author_data['lastname']
                )
            )
            author = result.scalar_one_or_none()
            
            if not author:
                # Créer nouvel auteur
                author = Author(
                    firstname=author_data.get('firstname'),
                    lastname=author_data['lastname']
                )
                session.add(author)
                await session.flush()
            
            # Créer la liaison
            pub_author = PublicationAuthor(
                publication_id=pub_id,
                author_id=author.id,
                author_order=i + 1,
                affiliation=author_data.get('affiliation')
            )
            session.add(pub_author)
    
    async def _add_keywords_to_publication(self, session: AsyncSession, pub_id: uuid.UUID, keywords_data: List[str]):
        """Ajouter des mots-clés à une publication"""
        if not keywords_data:
            return
            
        # Dédupliquer et nettoyer les mots-clés
        unique_keywords = set()
        for keyword_text in keywords_data:
            if keyword_text and keyword_text.strip():
                cleaned = keyword_text.strip()
                if len(cleaned) > 1:  # Au moins 2 caractères
                    unique_keywords.add(cleaned)
        
        logger.debug(f"Ajout de {len(unique_keywords)} mots-clés uniques")
        
        for keyword_text in unique_keywords:
            try:
                # Vérifier si le mot-clé existe
                result = await session.execute(
                    select(Keyword).where(Keyword.keyword == keyword_text)
                )
                keyword = result.scalar_one_or_none()
                
                if not keyword:
                    keyword = Keyword(keyword=keyword_text)
                    session.add(keyword)
                    await session.flush()
                
                # Vérifier si la relation existe déjà
                existing_relation = await session.execute(
                    select(PublicationKeyword).where(
                        PublicationKeyword.publication_id == pub_id,
                        PublicationKeyword.keyword_id == keyword.id
                    )
                )
                
                if not existing_relation.scalar_one_or_none():
                    # Créer la liaison seulement si elle n'existe pas
                    pub_keyword = PublicationKeyword(
                        publication_id=pub_id,
                        keyword_id=keyword.id
                    )
                    session.add(pub_keyword)
                else:
                    logger.debug(f"Mot-clé '{keyword_text}' déjà lié à la publication")
                    
            except Exception as e:
                logger.warning(f"Erreur ajout mot-clé '{keyword_text}': {e}")
                continue

    async def _add_mesh_terms_to_publication(self, session: AsyncSession, pub_id: uuid.UUID, mesh_terms_data: List[str]):
        """Ajouter des MeSH terms à une publication"""
        if not mesh_terms_data:
            return
            
        # Dédupliquer les MeSH terms
        unique_mesh_terms = set()
        for mesh_text in mesh_terms_data:
            if mesh_text and mesh_text.strip():
                cleaned = mesh_text.strip()
                if len(cleaned) > 1:
                    unique_mesh_terms.add(cleaned)
        
        for mesh_text in unique_mesh_terms:
            try:
                # Vérifier si le MeSH term existe
                result = await session.execute(
                    select(MeshTerm).where(MeshTerm.term == mesh_text)
                )
                mesh_term = result.scalar_one_or_none()
                
                if not mesh_term:
                    mesh_term = MeshTerm(term=mesh_text)
                    session.add(mesh_term)
                    await session.flush()
                
                # Vérifier si la relation existe déjà
                existing_relation = await session.execute(
                    select(PublicationMeshTerm).where(
                        PublicationMeshTerm.publication_id == pub_id,
                        PublicationMeshTerm.mesh_term_id == mesh_term.id
                    )
                )
                
                if not existing_relation.scalar_one_or_none():
                    # Créer la liaison
                    pub_mesh = PublicationMeshTerm(
                        publication_id=pub_id,
                        mesh_term_id=mesh_term.id
                    )
                    session.add(pub_mesh)
                    
            except Exception as e:
                logger.warning(f"Erreur ajout MeSH term '{mesh_text}': {e}")
                continue

    async def _add_text_sections_to_publication(self, session: AsyncSession, pub_id: uuid.UUID, sections_data: Dict[str, str]):
        """Ajouter des sections de texte à une publication"""
        if not sections_data:
            return
            
        for i, (section_name, content) in enumerate(sections_data.items()):
            # Validation du contenu
            if not content or not content.strip():
                continue
            
            # Validation et nettoyage du nom de section
            if not section_name or not section_name.strip():
                section_name = f"Section_{i+1}"
                logger.warning(f"Section name vide remplacé par {section_name}")
            
            # Nettoyer et limiter la longueur du nom de section
            section_name = section_name.strip()[:255]
            
            # Vérification finale
            if not section_name:
                section_name = f"Unnamed_Section_{i+1}"
                
            text_section = TextSection(
                publication_id=pub_id,
                section_name=section_name,
                content=content.strip(),
                section_order=i + 1
            )
            session.add(text_section)
    
    async def _publication_to_dict(self, session: AsyncSession, publication: Publication) -> Dict:
        """Convertir une publication en dictionnaire avec toutes les relations"""
        # Charger les auteurs
        authors_result = await session.execute(
            select(PublicationAuthor, Author)
            .join(Author)
            .where(PublicationAuthor.publication_id == publication.id)
            .order_by(PublicationAuthor.author_order)
        )
        authors = [
            {
                'firstname': author.firstname,
                'lastname': author.lastname,
                'affiliation': pub_author.affiliation
            }
            for pub_author, author in authors_result.all()
        ]
        
        # Charger les mots-clés
        keywords_result = await session.execute(
            select(Keyword)
            .join(PublicationKeyword)
            .where(PublicationKeyword.publication_id == publication.id)
        )
        keywords = [kw.keyword for kw in keywords_result.scalars().all()]
        
        # Charger les MeSH terms
        mesh_result = await session.execute(
            select(MeshTerm)
            .join(PublicationMeshTerm)
            .where(PublicationMeshTerm.publication_id == publication.id)
        )
        mesh_terms = [mesh.term for mesh in mesh_result.scalars().all()]
        
        return {
            'id': str(publication.id),
            'pmcid': publication.pmcid,
            'pmid': publication.pmid,
            'doi': publication.doi,
            'title': publication.title,
            'abstract': publication.abstract,
            'publication_date': publication.publication_date.isoformat() if publication.publication_date else None,
            'journal': publication.journal,
            'authors': authors,
            'keywords': keywords,
            'mesh_terms': mesh_terms,
            'created_at': publication.created_at.isoformat(),
            'updated_at': publication.updated_at.isoformat()
        }
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parser une date depuis string"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            return None


# Exemple d'utilisation
async def main():
    """Exemple d'utilisation du client"""
    client = DatabaseClient()
    
    try:
        # Créer les tables
        await client.create_tables()
        
        # Exemple de création de publication
        pub_data = {
            'pmcid': 'PMC1234567',
            'pmid': '12345678',
            'title': 'Test Publication',
            'abstract': 'This is a test abstract',
            'publication_date': '2023-01-01',
            'journal': 'Test Journal',
            'authors': [
                {'firstname': 'John', 'lastname': 'Doe', 'affiliation': 'Test University'},
                {'firstname': 'Jane', 'lastname': 'Smith', 'affiliation': 'Another University'}
            ],
            'keywords': ['bioscience', 'nasa', 'research'],
            'mesh_terms': ['Space Biology', 'Microgravity'],
            'full_text_sections': {
                'Introduction': 'This is the introduction...',
                'Methods': 'This is the methods section...'
            }
        }
        
        # Créer la publication
        pub_id = await client.create_publication(pub_data)
        print(f"Publication créée avec ID: {pub_id}")
        
        # Rechercher la publication
        result = await client.get_publication_by_pmcid('PMC1234567')
        print(f"Publication trouvée: {result['title']}")
        
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
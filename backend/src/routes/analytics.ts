import { PrismaClient } from "@prisma/client";
import { Router } from "express";
import { cacheMiddleware } from "../middleware/cache";

const prisma = new PrismaClient();
const router = Router();

// GET /api/analytics/overview - Vue d'ensemble des statistiques
router.get("/overview", cacheMiddleware({ ttl: 3600 }), async (req, res) => {
  try {
    const [
      totalPublications,
      uniqueKeywords,
      uniqueMeshTerms,
      dateRange
    ] = await Promise.all([
      // Total des publications
      prisma.publications.count(),
      
      // Nombre de keywords uniques
      prisma.keywords.count(),
      
      // Nombre de MeSH terms uniques
      prisma.mesh_terms.count(),
      
      // Date range
      prisma.publications.aggregate({
        _min: { publication_date: true },
        _max: { publication_date: true }
      })
    ]);

    const minYear = dateRange._min.publication_date ? new Date(dateRange._min.publication_date).getFullYear() : null;
    const maxYear = dateRange._max.publication_date ? new Date(dateRange._max.publication_date).getFullYear() : null;

    res.json({
      totalPublications,
      uniqueKeywords,
      uniqueMeshTerms,
      timeSpan: minYear && maxYear ? `${minYear}-${maxYear}` : "N/A",
      minYear,
      maxYear
    });
  } catch (error) {
    console.error("Error fetching overview:", error);
    res.status(500).json({ error: "Failed to fetch overview statistics" });
  }
});

// GET /api/analytics/timeline - Évolution temporelle des publications
router.get("/timeline", cacheMiddleware({ ttl: 3600 }), async (req, res) => {
  try {
    const timeline = await prisma.$queryRaw<Array<{ year: number; count: bigint }>>`
      SELECT 
        EXTRACT(YEAR FROM publication_date)::integer as year,
        COUNT(*)::bigint as count
      FROM publications
      WHERE publication_date IS NOT NULL
      GROUP BY year
      ORDER BY year ASC
    `;

    // Convertir les bigint en number pour JSON
    const formattedTimeline = timeline.map(item => ({
      year: item.year,
      count: Number(item.count)
    }));

    res.json(formattedTimeline);
  } catch (error) {
    console.error("Error fetching timeline:", error);
    res.status(500).json({ error: "Failed to fetch timeline" });
  }
});

// GET /api/analytics/distribution/keywords - Top keywords
router.get("/distribution/keywords", cacheMiddleware({ ttl: 3600 }), async (req, res) => {
  try {
    const limit = parseInt(req.query.limit as string) || 20;
    
    const distribution = await prisma.$queryRaw<Array<{ keyword: string; count: bigint }>>`
      SELECT 
        k.keyword,
        COUNT(*)::bigint as count
      FROM keywords k
      INNER JOIN publication_keywords pk ON k.id = pk.keyword_id
      GROUP BY k.keyword
      ORDER BY count DESC
      LIMIT ${limit}
    `;

    const formatted = distribution.map(item => ({
      name: item.keyword,
      count: Number(item.count)
    }));

    res.json(formatted);
  } catch (error) {
    console.error("Error fetching keyword distribution:", error);
    res.status(500).json({ error: "Failed to fetch keyword distribution" });
  }
});

// GET /api/analytics/distribution/mesh-terms - Top MeSH terms
router.get("/distribution/mesh-terms", cacheMiddleware({ ttl: 3600 }), async (req, res) => {
  try {
    const limit = parseInt(req.query.limit as string) || 20;
    
    const distribution = await prisma.$queryRaw<Array<{ term: string; count: bigint }>>`
      SELECT 
        m.term,
        COUNT(*)::bigint as count
      FROM mesh_terms m
      INNER JOIN publication_mesh_terms pm ON m.id = pm.mesh_term_id
      GROUP BY m.term
      ORDER BY count DESC
      LIMIT ${limit}
    `;

    const formatted = distribution.map(item => ({
      name: item.term,
      count: Number(item.count)
    }));

    res.json(formatted);
  } catch (error) {
    console.error("Error fetching mesh term distribution:", error);
    res.status(500).json({ error: "Failed to fetch mesh term distribution" });
  }
});

// GET /api/analytics/distribution/entities - Distribution par type d'entité
router.get("/distribution/entities", cacheMiddleware({ ttl: 3600 }), async (req, res) => {
  try {
    console.log("Fetching entity distribution...");
    
    // Vérifier si la table entities a des données
    const entityCount = await prisma.entities.count();
    console.log(`Total entities in database: ${entityCount}`);
    
    if (entityCount === 0) {
      console.log("No entities found in database, returning empty array");
      return res.json([]);
    }
    
    const distribution = await prisma.entities.groupBy({
      by: ['entity_type'],
      _count: {
        entity_type: true,
      },
      orderBy: {
        _count: {
          entity_type: 'desc',
        },
      },
    });

    const formatted = distribution.map(item => ({
      name: item.entity_type,
      count: item._count.entity_type
    }));
    
    console.log("Entity distribution result:", formatted);
    res.json(formatted);
  } catch (error) {
    console.error("Error fetching entity distribution:", error);
    // Retourner un tableau vide en cas d'erreur plutôt qu'une erreur 500
    res.json([]);
  }
});

// GET /api/analytics/top-entities - Top entités par type
router.get("/top-entities", cacheMiddleware({ ttl: 3600 }), async (req, res) => {
  try {
    const entityType = req.query.type as string;
    const limit = parseInt(req.query.limit as string) || 15;
    
    // Vérifier si la table entities a des données
    const entityCount = await prisma.entities.count();
    console.log(`Top entities - Total entities in database: ${entityCount}`);
    
    if (entityCount === 0) {
      console.log("No entities found in database, returning empty array");
      return res.json([]);
    }
    
    let query;
    if (entityType) {
      query = prisma.$queryRaw<Array<{ entity_name: string; entity_type: string; count: bigint }>>`
        SELECT 
          e.entity_name,
          e.entity_type,
          COUNT(DISTINCT pe.publication_id)::bigint as count
        FROM entities e
        INNER JOIN publication_entities pe ON e.id = pe.entity_id
        WHERE e.entity_type = ${entityType}
        GROUP BY e.entity_name, e.entity_type
        ORDER BY count DESC
        LIMIT ${limit}
      `;
    } else {
      query = prisma.$queryRaw<Array<{ entity_name: string; entity_type: string; count: bigint }>>`
        SELECT 
          e.entity_name,
          e.entity_type,
          COUNT(DISTINCT pe.publication_id)::bigint as count
        FROM entities e
        INNER JOIN publication_entities pe ON e.id = pe.entity_id
        GROUP BY e.entity_name, e.entity_type
        ORDER BY count DESC
        LIMIT ${limit}
      `;
    }

    const topEntities = await query;

    const formatted = topEntities.map(item => ({
      name: item.entity_name,
      type: item.entity_type,
      count: Number(item.count)
    }));

    res.json(formatted);
  } catch (error) {
    console.error("Error fetching top entities:", error);
    // Retourner un tableau vide en cas d'erreur plutôt qu'une erreur 500
    res.json([]);
  }
});

// GET /api/analytics/publications-by-year-range - Publications par période
router.get("/publications-by-year-range", cacheMiddleware({ ttl: 3600 }), async (req, res) => {
  try {
    const ranges = await prisma.$queryRaw<Array<{ range: string; count: bigint }>>`
      SELECT 
        CASE 
          WHEN EXTRACT(YEAR FROM publication_date) < 2000 THEN '1980-1999'
          WHEN EXTRACT(YEAR FROM publication_date) BETWEEN 2000 AND 2009 THEN '2000-2009'
          WHEN EXTRACT(YEAR FROM publication_date) BETWEEN 2010 AND 2019 THEN '2010-2019'
          WHEN EXTRACT(YEAR FROM publication_date) >= 2020 THEN '2020-2024'
          ELSE 'Unknown'
        END as range,
        COUNT(*)::bigint as count
      FROM publications
      WHERE publication_date IS NOT NULL
      GROUP BY range
      ORDER BY range
    `;

    const formatted = ranges.map(item => ({
      range: item.range,
      count: Number(item.count)
    }));

    res.json(formatted);
  } catch (error) {
    console.error("Error fetching year ranges:", error);
    res.status(500).json({ error: "Failed to fetch year range data" });
  }
});

export default router;

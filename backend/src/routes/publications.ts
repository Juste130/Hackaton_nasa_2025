import { PrismaClient } from "@prisma/client";
import { Router } from "express";

const prisma = new PrismaClient();
const router = Router();

// GET /api/publications
router.get("/publications", async (req, res) => {
  const { title, author, journal, from, to, skip, take, phenomenon, mission, organism } = req.query as Record<string, string | undefined>;

  const filters: any = {};

  if (title) {
    filters.title = { contains: String(title), mode: "insensitive" };
  }
  if (journal) {
    filters.journal = { contains: String(journal), mode: "insensitive" };
  }
  if (from || to) {
    filters.publication_date = {};
    if (from) (filters.publication_date as any).gte = new Date(String(from));
    if (to) (filters.publication_date as any).lte = new Date(String(to));
  }

  // Ajout du filtrage par mission
  if (mission) {
    filters.mission = { contains: String(mission), mode: "insensitive" };
  }

  // Ajout du filtrage par organisme
  if (organism) {
    filters.organisms = { has: String(organism) };
  }

  // Ajout du filtrage par phénomène
  if (phenomenon) {
    filters.phenomena = { has: String(phenomenon) };
  }

  let authorFilter = undefined as any;
  if (author) {
    authorFilter = {
      publication_authors: {
        some: {
          authors: {
            OR: [
              { firstname: { contains: String(author), mode: "insensitive" } },
              { lastname: { contains: String(author), mode: "insensitive" } },
            ],
          },
        },
      },
    };
  }

  const parsedSkip = Number.isFinite(Number(skip)) ? Number(skip) : undefined;
  const parsedTake = Number.isFinite(Number(take)) ? Number(take) : undefined;

  try {
    const publications = await prisma.publications.findMany({
      where: {
        ...filters,
        ...(authorFilter || {}),
      },
      include: {
        publication_authors: { include: { authors: true } },
        publication_mesh_terms: true,
        publication_keywords: true,
        publication_entities: true,
        text_sections: true,
      },
      orderBy: { publication_date: "desc" },
      skip: parsedSkip,
      take: parsedTake,
    });
    res.json(publications);
  } catch (error) {
    res.status(500).json({ error: error });
  }
});

export default router;

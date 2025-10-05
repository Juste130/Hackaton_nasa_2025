import { PrismaClient } from "@prisma/client";
import cors from "cors";
import express from "express";

const prisma = new PrismaClient();
const app = express();
app.use(cors());
app.use(express.json());

// Récupérer toutes les publications avec filtres optionnels
app.get("/api/publications", async (req, res) => {
  const { title, author, journal, from, to } = req.query;

  const filters: any = {};

  if (title) {
    filters.title = { contains: String(title), mode: "insensitive" };
  }
  if (journal) {
    filters.journal = { contains: String(journal), mode: "insensitive" };
  }
  if (from || to) {
    filters.publication_date = {};
    if (from) filters.publication_date.gte = new Date(String(from));
    if (to) filters.publication_date.lte = new Date(String(to));
  }

  // Filtrage par auteur (nom/prénom)
  let authorFilter = undefined;
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

  try {
    const publications = await prisma.publications.findMany({
      where: {
        ...filters,
        ...(authorFilter || {}),
      },
      include: {
        publication_authors: {
          include: { authors: true },
        },
      },
      orderBy: { publication_date: "desc" },
    });
    res.json(publications);
  } catch (error) {
    res
      .status(500)
      .json({ error: "Erreur lors de la récupération des publications" });
  }
});

app.get("/", (req, res) => {
  res.send("Hello World");
});

// Lancer le serveur
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Serveur lancé sur http://localhost:${PORT}`);
});

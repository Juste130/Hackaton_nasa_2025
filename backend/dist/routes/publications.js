"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const client_1 = require("@prisma/client");
const express_1 = require("express");
const axios_1 = __importDefault(require("axios"));
const prisma = new client_1.PrismaClient();
const router = (0, express_1.Router)();
// URL de l'API Neo4j (Python sur port 8000)
const NEO4J_API_URL = process.env.NEO4J_API_URL || "http://localhost:8000";
// GET /api/publications
router.get("/publications", async (req, res) => {
    const { title, author, journal, from, to, skip, take, organism, phenomenon } = req.query;
    const filters = {};
    if (title) {
        filters.title = { contains: String(title), mode: "insensitive" };
    }
    if (journal) {
        filters.journal = { contains: String(journal), mode: "insensitive" };
    }
    if (from || to) {
        filters.publication_date = {};
        if (from)
            filters.publication_date.gte = new Date(String(from));
        if (to)
            filters.publication_date.lte = new Date(String(to));
    }
    // Filtre par organism ou phenomenon via Neo4j
    if (organism || phenomenon) {
        try {
            const filterRequest = {
                node_types: ["Publication"],
                filters: {
                    organisms: organism ? [organism] : [],
                    phenomena: phenomenon ? [phenomenon] : [],
                },
                limit: 30,
            };
            const response = await axios_1.default.post(`${NEO4J_API_URL}/api/graph/filter`, filterRequest);
            const nodes = response.data.nodes || [];
            const pmcids = nodes
                .filter((node) => node.label === "Publication")
                .map((node) => node.properties.pmcid)
                .filter(Boolean);
            console.log("Ok");
            console.log(pmcids);
            if (pmcids.length > 0) {
                filters.pmcid = { in: pmcids };
            }
            else {
                // Aucune publication trouvée dans Neo4j avec ces filtres
                return res.json([]);
            }
        }
        catch (error) {
            console.error("Error filtering via Neo4j:", error);
            return res.status(500).json({ error: "Failed to apply graph filters" });
        }
    }
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
    const parsedSkip = Number.isFinite(Number(skip)) ? Number(skip) : 0;
    const parsedTake = Number.isFinite(Number(take)) ? Number(take) : 50; // Limite par défaut de 50
    try {
        const publications = await prisma.publications.findMany({
            where: {
                ...filters,
                ...(authorFilter || {}),
            },
            include: {
                publication_authors: {
                    include: {
                        authors: {
                            select: {
                                id: true,
                                firstname: true,
                                lastname: true,
                                orcid: true
                            }
                        }
                    }
                },
                publication_mesh_terms: {
                    take: 4, // Limite à 4 mesh terms par publication
                    orderBy: {
                        is_major_topic: 'desc' // Priorise les topics majeurs
                    },
                    select: {
                        mesh_terms: {
                            select: {
                                id: true,
                                term: true
                            }
                        }
                    }
                },
                publication_keywords: {
                    select: {
                        keywords: {
                            select: {
                                id: true,
                                keyword: true
                            }
                        }
                    }
                },
                publication_entities: {
                    select: {
                        id: true,
                        confidence: true,
                        entities: {
                            select: {
                                id: true,
                                entity_type: true,
                                entity_name: true
                            }
                        }
                    }
                },
                // text_sections sont retirées par défaut car très volumineuses
                // Utilisez une route dédiée pour charger les détails complets d'une publication
            },
            orderBy: { publication_date: "desc" },
            skip: parsedSkip,
            take: parsedTake,
        });
        res.json(publications);
    }
    catch (error) {
        res.status(500).json({ error: error });
    }
});
// GET /api/publications/:id - Obtenir une publication spécifique avec tous ses détails
router.get("/publications/:id", async (req, res) => {
    const { id } = req.params;
    try {
        const publication = await prisma.publications.findUnique({
            where: { id: String(id) },
            include: {
                publication_authors: {
                    include: {
                        authors: {
                            select: {
                                id: true,
                                firstname: true,
                                lastname: true,
                                email: true,
                                orcid: true,
                            },
                        },
                    },
                    orderBy: {
                        author_order: 'asc',
                    },
                },
                publication_mesh_terms: {
                    include: {
                        mesh_terms: {
                            select: {
                                id: true,
                                term: true,
                                tree_number: true,
                            },
                        },
                    },
                    orderBy: {
                        is_major_topic: 'desc',
                    },
                },
                publication_keywords: {
                    include: {
                        keywords: {
                            select: {
                                id: true,
                                keyword: true,
                                category: true,
                            },
                        },
                    },
                },
                publication_entities: {
                    include: {
                        entities: {
                            select: {
                                id: true,
                                entity_type: true,
                                entity_name: true,
                                normalized_name: true,
                                description: true,
                            },
                        },
                    },
                    orderBy: {
                        confidence: 'desc',
                    },
                },
                text_sections: {
                    select: {
                        id: true,
                        section_name: true,
                        content: true,
                        section_order: true,
                    },
                    orderBy: {
                        section_order: 'asc',
                    },
                },
            },
        });
        if (!publication) {
            return res.status(404).json({ error: "Publication not found" });
        }
        res.json(publication);
    }
    catch (error) {
        console.error("Error fetching publication details:", error);
        res.status(500).json({ error: "Failed to fetch publication details" });
    }
});
// GET /api/publications/pmcid/:pmcid - Obtenir une publication par PMCID
router.get("/publications/pmcid/:pmcid", async (req, res) => {
    const { pmcid } = req.params;
    try {
        const publication = await prisma.publications.findUnique({
            where: { pmcid: String(pmcid) },
            include: {
                publication_authors: {
                    include: {
                        authors: {
                            select: {
                                id: true,
                                firstname: true,
                                lastname: true,
                                email: true,
                                orcid: true,
                            },
                        },
                    },
                    orderBy: {
                        author_order: 'asc',
                    },
                },
                publication_mesh_terms: {
                    include: {
                        mesh_terms: {
                            select: {
                                id: true,
                                term: true,
                                tree_number: true,
                            },
                        },
                    },
                    orderBy: {
                        is_major_topic: 'desc',
                    },
                },
                publication_keywords: {
                    include: {
                        keywords: {
                            select: {
                                id: true,
                                keyword: true,
                                category: true,
                            },
                        },
                    },
                },
                publication_entities: {
                    include: {
                        entities: {
                            select: {
                                id: true,
                                entity_type: true,
                                entity_name: true,
                                normalized_name: true,
                                description: true,
                            },
                        },
                    },
                    orderBy: {
                        confidence: 'desc',
                    },
                },
            },
        });
        if (!publication) {
            return res.status(404).json({ error: "Publication not found" });
        }
        res.json(publication);
    }
    catch (error) {
        console.error("Error fetching publication by PMCID:", error);
        res.status(500).json({ error: "Failed to fetch publication details" });
    }
});
exports.default = router;

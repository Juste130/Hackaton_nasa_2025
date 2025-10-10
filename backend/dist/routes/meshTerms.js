"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const client_1 = require("@prisma/client");
const express_1 = require("express");
const prisma = new client_1.PrismaClient();
const router = (0, express_1.Router)();
router.get("/:id", async (req, res) => {
    const { id } = req.params;
    // Validation basique de l'UUID
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(id)) {
        return res.status(400).json({
            error: "Invalid UUID format",
            message: "The provided ID is not a valid UUID"
        });
    }
    try {
        const meshTerm = await prisma.mesh_terms.findUnique({
            where: {
                id: id,
            },
            include: {
                publication_mesh_terms: {
                    include: {
                        publications: {
                            select: {
                                id: true,
                                title: true,
                                pmcid: true
                            }
                        }
                    }
                }
            }
        });
        if (!meshTerm) {
            return res.status(404).json({
                error: "Mesh term not found",
                message: `No mesh term found with ID: ${id}`
            });
        }
        res.json(meshTerm);
    }
    catch (error) {
        console.error("Error fetching mesh term:", error);
        res.status(500).json({
            error: "Internal server error",
            message: error instanceof Error ? error.message : "Unknown error"
        });
    }
});
exports.default = router;

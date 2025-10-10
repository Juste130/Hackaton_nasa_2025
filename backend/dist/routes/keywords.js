"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const client_1 = require("@prisma/client");
const express_1 = require("express");
const prisma = new client_1.PrismaClient();
const router = (0, express_1.Router)();
router.get("/keywords/:id", async (req, res) => {
    const { id } = req.params;
    const keywords = await prisma.keywords.findMany({
        where: {
            id: id,
        },
    });
    res.json(keywords);
    console.log(keywords);
});
exports.default = router;

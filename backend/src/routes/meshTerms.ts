import { PrismaClient } from "@prisma/client";
import { Router } from "express";

const prisma = new PrismaClient();
const router = Router();

router.get("/:id", async (req, res) => {
  const { id } = req.params as { id: string };

  const meshTerms = await prisma.mesh_terms.findMany({
    where: {
      id: id,
    },
  });
  res.json(meshTerms);
});

export default router;

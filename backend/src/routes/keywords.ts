import { PrismaClient } from "@prisma/client";
import { Router } from "express";

const prisma = new PrismaClient();
const router = Router();

router.get("/keywords/:id", async (req, res) => {
  const { id } = req.params as { id: string };
  const keywords = await prisma.keywords.findMany({
    where: {
      id: id,
    },
  });
  res.json(keywords);
  console.log(keywords);
});

export default router;

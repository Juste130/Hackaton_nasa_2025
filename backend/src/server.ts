import cors from "cors";
import express from "express";
import keywordsRouter from "./routes/keywords";
import meshTermsRouter from "./routes/meshTerms";
import publicationsRouter from "./routes/publications";

const app = express();
app.use(cors());
app.use(express.json());

// Health check
app.get("/", (req, res) => {
  res.send("Hello World");
});

// Routes
app.use("/api", publicationsRouter);
app.use("/api/keywords", keywordsRouter);
app.use("/api/mesh_terms", meshTermsRouter);

// Lancer le serveur
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Serveur lancé sur http://localhost:${PORT}`);
});

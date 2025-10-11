import cors from "cors";
import express from "express";
import keywordsRouter from "./routes/keywords";
import meshTermsRouter from "./routes/meshTerms";
import publicationsRouter from "./routes/publications";
import filtersRouter from "./routes/filters";
import analyticsRouter from "./routes/analytics";
import { cacheService } from "./services/cache";
import { defaultCache } from "./middleware/cache";

const app = express();
app.use(cors());
app.use(express.json());

// Initialiser Redis
async function initializeServices() {
  try {
    await cacheService.connect();
    console.log('✅ Cache service initialized');
  } catch (error) {
    console.error('❌ Failed to initialize cache service:', error);
    console.log('⚠️ Server will run without cache');
  }
}

// Health check
app.get("/", (req, res) => {
  res.json({
    status: "OK",
    message: "NASA Hackathon 2025 API",
    cache: cacheService.isConnected() ? "connected" : "disconnected",
    timestamp: new Date().toISOString()
  });
});

// Health check pour le cache
app.get("/health/cache", (req, res) => {
  res.json({
    cache_connected: cacheService.isConnected(),
    timestamp: new Date().toISOString()
  });
});

// Routes avec cache
app.use("/api", defaultCache, publicationsRouter);
app.use("/api/keywords", defaultCache, keywordsRouter);
app.use("/api/mesh_terms", defaultCache, meshTermsRouter);
app.use("/api/filters", defaultCache, filtersRouter);
app.use("/api/analytics", defaultCache, analyticsRouter);

// Gestion graceful du shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, shutting down gracefully');
  await cacheService.disconnect();
  process.exit(0);
});

process.on('SIGINT', async () => {
  console.log('SIGINT received, shutting down gracefully');
  await cacheService.disconnect();
  process.exit(0);
});

// Lancer le serveur
const PORT = process.env.PORT || 3000;

async function startServer() {
  await initializeServices();
  
  app.listen(PORT, () => {
    console.log(`🚀 Serveur lancé sur http://localhost:${PORT}`);
    console.log(`📚 API Documentation: http://localhost:${PORT}/api/publications`);
  });
}

startServer().catch(console.error);

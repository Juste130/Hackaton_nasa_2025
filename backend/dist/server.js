"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const cors_1 = __importDefault(require("cors"));
const express_1 = __importDefault(require("express"));
const keywords_1 = __importDefault(require("./routes/keywords"));
const meshTerms_1 = __importDefault(require("./routes/meshTerms"));
const publications_1 = __importDefault(require("./routes/publications"));
const filters_1 = __importDefault(require("./routes/filters"));
const app = (0, express_1.default)();
app.use((0, cors_1.default)());
app.use(express_1.default.json());
// Health check
app.get("/", (req, res) => {
    res.send("Hello World");
});
// Routes
app.use("/api", publications_1.default);
app.use("/api/keywords", keywords_1.default);
app.use("/api/mesh_terms", meshTerms_1.default);
app.use("/api/filters", filters_1.default);
// Lancer le serveur
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Serveur lancé sur http://localhost:${PORT}`);
});

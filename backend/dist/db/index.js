"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.connectToDatabase = void 0;
const client_1 = require("@prisma/client");
const prisma = new client_1.PrismaClient();
const connectToDatabase = async () => {
    try {
        await prisma.$connect();
        console.log('Connected to the PostgreSQL database successfully.');
    }
    catch (error) {
        console.error('Error connecting to the database:', error);
        throw error;
    }
};
exports.connectToDatabase = connectToDatabase;
exports.default = prisma;

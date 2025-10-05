import express from 'express';
import { PrismaClient } from '@prisma/client';
import db from './db';

const app = express();
const prisma = new PrismaClient();

app.use(express.json());

// Define routes here
app.get('/', (req, res) => {
    res.send('Hello, World!');
});

// Connect to the database
db(prisma)
    .then(() => {
        const PORT = process.env.PORT || 3000;
        app.listen(PORT, () => {
            console.log(`Server is running on http://localhost:${PORT}`);
        });
    })
    .catch((error:any) => {
        console.error('Database connection error:', error);
    });
# Project Title

A brief description of your project.

## Prerequisites

- Node.js (version X.X.X or higher)
- PostgreSQL (version X.X.X or higher)
- Prisma (installed globally or as a project dependency)

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   ```

2. Navigate to the backend directory:
   ```
   cd backend
   ```

3. Install the dependencies:
   ```
   npm install
   ```

4. Set up your PostgreSQL database and update the connection details in `prisma/schema.prisma`.

## Database Setup

1. Run the following command to generate the Prisma client:
   ```
   npx prisma generate
   ```

2. Apply the migrations to your database:
   ```
   npx prisma migrate dev --name init
   ```

## Running the Application

To start the server, run:
```
npm start
```

The server will be running on `http://localhost:3000`.

## Usage

- Define your API routes in `src/server.ts`.
- Use the Prisma client instance from `src/prisma/client.ts` to interact with your database.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
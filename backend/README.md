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

In development (TypeScript with ts-node):

```
npm run dev
```

In production (after build):

```
npm run build && npm start
```

The server runs on `http://localhost:3001` by default.

## Usage

- Define your API routes in `src/server.ts`.
- Use the Prisma client instance from `src/prisma/client.ts` to interact with your database.

## API Reference

### GET `/publications`

Returns publications with optional filters. Results include associated authors via the `publication_authors` relation.

Query parameters (all optional):

- `title` (string): partial match on publication title (case-insensitive)
- `journal` (string): partial match on journal name (case-insensitive)
- `author` (string): partial match on author `firstname` OR `lastname` (case-insensitive)
- `from` (date ISO or yyyy-mm-dd): filter `publication_date >= from`
- `to` (date ISO or yyyy-mm-dd): filter `publication_date <= to`

Sorting:

- Default order: `publication_date` descending.

Pagination:

- Not implemented yet (all matching records are returned). Consider adding `take`/`skip` if needed.

Example requests:

```
# All publications
curl "http://localhost:3001/publications"

# Filter by title contains "Mars"
curl "http://localhost:3001/publications?title=Mars"

# Filter by author name contains "Smith"
curl "http://localhost:3001/publications?author=Smith"

# Filter by journal and date range
curl "http://localhost:3001/publications?journal=Nature&from=2022-01-01&to=2024-12-31"
```

Response shape:

```
[
  {
    "id": "uuid",
    "pmcid": "string",
    "pmid": "string | null",
    "doi": "string | null",
    "title": "string",
    "abstract": "string | null",
    "publication_date": "YYYY-MM-DD | null",
    "journal": "string | null",
    "created_at": "ISO datetime",
    "updated_at": "ISO datetime",
    "abstract_generated": "string | null",
    "generation_type": "string | null",
    "key_findings": "string | null",
    "methodology": "string | null",
    "full_text_content": "string | null",
    "embedding": null,
    "publication_authors": [
      {
        "publication_id": "uuid",
        "author_id": "uuid",
        "author_order": number,
        "affiliation": "string | null",
        "authors": {
          "id": "uuid",
          "firstname": "string | null",
          "lastname": "string",
          "email": "string | null",
          "orcid": "string | null",
          "created_at": "ISO datetime"
        }
      }
    ]
  }
]
```

Notes:

- The `embedding` fields are `vector` in the database and are returned as `null` or omitted depending on your driver configuration.
- The endpoint currently only expands `publication_authors -> authors`. Other relations (`publication_entities`, `publication_keywords`, `publication_mesh_terms`, `text_sections`) are not included in the response but can be added if needed.

Errors:

- `500` `{ "error": "Erreur lors de la récupération des publications" }` on server/database failures.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

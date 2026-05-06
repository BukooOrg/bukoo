# Bruno Test Collection

## Folder Structure

```
bruno/
├── bruno.json                     ← collection root
├── environments/
│   ├── local.bru                  ← local env vars (baseUrl, apiBase, credentials)
│   └── staging.bru
├── <api_set_folder>/              ← one folder per API set (e.g. auth/, health/)
│   ├── folder.bru                 ← API set metadata (name, auth mode)
│   └── <use_case_name>/           ← one subfolder per use case
│       ├── folder.bru             ← use case metadata (name, seq)
│       ├── 01_success.bru         ← happy path — always seq 1
│       ├── 02_<error>.bru         ← first error case — seq 2
│       ├── 03_<error>.bru         ← second error case — seq 3
│       └── …
```

## File Naming Rules

- Use case subfolders: `snake_case` (e.g., `register_customer/`, `log_out/`)
- Test files: `NN_<snake_case_description>.bru` with zero-padded two-digit prefix
- The happy path is always `01_success.bru`
- Error case filenames describe the invalid condition (e.g., `02_invalid_email.bru`, `07_duplicate_email.bru`)

## Sequence Numbers

`meta.seq` inside each `.bru` file **must match** its numeric filename prefix. Bruno uses seq to order requests within a folder — a mismatch causes wrong execution order.

| File                    | meta.seq |
| ----------------------- | -------- |
| `01_success.bru`        | 1        |
| `02_invalid_email.bru`  | 2        |
| `03_password_too_short.bru` | 3    |
| …                       | …        |

The `folder.bru` inside a use case subfolder also has a `seq` — it determines the order of use case folders within their parent API set folder. Check existing sibling `folder.bru` files to find the next available seq.

## folder.bru Format

**API set folder** (`bruno/<api_set>/folder.bru`):
```bru
meta {
  name: [Human Readable API Set Name]
}

auth {
  mode: none
}
```

**Use case subfolder** (`bruno/<api_set>/<use_case>/folder.bru`):
```bru
meta {
  name: [Human Readable Use Case Name]
  seq: [N]
}
```

## Test File Format

```bru
meta {
  name: [human readable scenario name]
  type: http
  seq: [N]
}

[get|post|patch|put|delete] {
  url: {{baseUrl}}{{apiBase}}/[path]
  body: [none|json]
  auth: [none|bearer]
}

auth:bearer {
  token: {{token}}
}

headers {
  Content-Type: application/json
}

body:json {
  // [scenario description]
  {
    "field": "value"
  }
}

script:post-response {
  if (res.status === 200) {
    bru.setEnvVar("token", res.body.data.access_token);
  }
}

tests {
  test("status 201", function() {
    expect(res.status).to.equal(201);
  });

  test("success flag is true", function() {
    expect(res.body.success).to.be.true;
  });

  test("meta has requestId", function() {
    expect(res.body.meta.requestId).to.be.a("string");
  });
}
```

## Key Conventions

- Always use `{{baseUrl}}{{apiBase}}` for URLs — never hardcode.
- Always use `{{token}}` for Bearer auth headers.
- Add a comment inside `body:json` naming the scenario (e.g., `// duplicate email`).
- If a test relies on state from a previous file (e.g., `07_duplicate_email.bru` requires `01_success.bru` to have registered the user first), note the dependency in a comment.
- `script:post-response` is only needed when a response value (e.g., `access_token`) must be stored in an env var for subsequent requests.
- `auth:bearer` block is only needed when `auth: bearer` is set in the method block.

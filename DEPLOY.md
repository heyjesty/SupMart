# Deploying SupMart to Vercel

Vercel runs Django as a serverless function. Its filesystem is read-only, so production needs two services:

| What | Where | Why |
|---|---|---|
| Database | **Supabase Postgres** | `db.sqlite3` can't be written to on Vercel |
| Uploaded images (products, categories, profile photos) | **Supabase Storage** | the `media/` folder can't be written to on Vercel |
| CSS / JS / theme images | bundled with the app, served by WhiteNoise | no extra service needed |

Locally nothing changes: with no environment variables set, the site still uses SQLite and the `media/` folder.

---

## 1. Create the Supabase project (free)

1. Sign up at <https://supabase.com> → **New project**. Pick a region close to your customers (e.g. *South Asia (Mumbai)*) and save the database password.
2. **Database URL**: click **Connect** (top bar) → **Transaction pooler** → copy the URI. It looks like
   `postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres`
   Replace `[YOUR-PASSWORD]` with your database password.
3. **Storage bucket**: **Storage** → **New bucket** → name it `media` → turn **Public bucket** on → **Create**.
4. **Storage keys**: **Storage** → **Settings** (S3 Connection):
   - copy the **Endpoint** (`https://<project-ref>.supabase.co/storage/v1/s3`) and **Region**
   - under **S3 Access Keys** → **New access key** → copy the **Access key ID** and **Secret access key** (the secret is shown only once)

## 2. Copy your current data into Supabase

Run these in **PowerShell** from the project folder.

```powershell
# 2a. Export everything from the local SQLite database (run BEFORE setting DATABASE_URL)
python manage.py dumpdata --natural-foreign --exclude contenttypes --exclude auth.permission --exclude admin.logentry --exclude sessions --indent 2 -o data.json

# 2b. Point this terminal at Supabase (values from step 1)
$env:DATABASE_URL = "postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres"
$env:MEDIA_BUCKET = "media"
$env:MEDIA_ENDPOINT_URL = "https://<project-ref>.supabase.co/storage/v1/s3"
$env:MEDIA_REGION = "<region>"
$env:MEDIA_ACCESS_KEY_ID = "<access key id>"
$env:MEDIA_SECRET_ACCESS_KEY = "<secret access key>"
$env:MEDIA_PUBLIC_DOMAIN = "<project-ref>.supabase.co/storage/v1/object/public/media"

# 2c. Create the tables, load the data, upload the images
python manage.py migrate
python manage.py loaddata data.json
python manage.py upload_media
```

`data.json` contains customer emails and password hashes. It is git-ignored; delete it once the import works.
Close this terminal afterwards (or open a new one) so your local site goes back to SQLite.

## 3. Deploy on Vercel

1. Commit and push the project to GitHub (`git push origin main`).
2. Go to <https://vercel.com/new> → **Import** the `SupMart` repository.
   - Framework Preset: **Other**
   - Leave the build and output settings empty (`vercel.json` handles it).
3. Open **Environment Variables** and add:

   | Name | Value |
   |---|---|
   | `DJANGO_SECRET_KEY` | a new random string: `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
   | `DATABASE_URL` | from step 1.2 |
   | `MEDIA_BUCKET` | `media` |
   | `MEDIA_ENDPOINT_URL` | from step 1.4 |
   | `MEDIA_REGION` | from step 1.4 |
   | `MEDIA_ACCESS_KEY_ID` | from step 1.4 |
   | `MEDIA_SECRET_ACCESS_KEY` | from step 1.4 |
   | `MEDIA_PUBLIC_DOMAIN` | `<project-ref>.supabase.co/storage/v1/object/public/media` |

4. Click **Deploy**. When it finishes, open `https://<your-project>.vercel.app`.

Every later `git push` to `main` redeploys automatically.

### Custom domain (optional)
Add it under Vercel → **Settings → Domains**, then add two more environment variables and redeploy:

```
DJANGO_ALLOWED_HOSTS=.vercel.app,www.yourdomain.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://*.vercel.app,https://www.yourdomain.com
```

## 4. After changing models

Vercel doesn't run migrations. When you add a migration, apply it to Supabase from your machine before (or right after) pushing:

```powershell
$env:DATABASE_URL = "<supabase url>"
python manage.py migrate
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `400 Bad Request` | The domain isn't in `DJANGO_ALLOWED_HOSTS`. |
| `403 CSRF verification failed` on forms | Add your domain to `DJANGO_CSRF_TRUSTED_ORIGINS`. |
| `500` on every page | Check Vercel → **Logs**. Usually a wrong `DATABASE_URL` or missing migrations (step 2c). |
| Product images broken | Make sure the bucket is **public**, `MEDIA_PUBLIC_DOMAIN` is correct, and `upload_media` ran. |
| Need detailed errors temporarily | Set `DJANGO_DEBUG=True`, redeploy, then **remove it** again. |

## Good to know
- Vercel's free **Hobby** plan is for non-commercial use. A shop taking real orders needs the **Pro** plan.
- Serverless functions "sleep" when idle, so the first request after a quiet period takes 1–3 seconds.
- Supabase's free tier pauses a project after 7 days without activity. Unpause it from the dashboard.

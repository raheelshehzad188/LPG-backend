# GitHub par push kaise karein

## 1. Pehle naya repo banao (zaroori)
1. https://github.com/new par jao
2. Repository name: **LGP-backend** (exact)
3. Description: Lahore Property Guide Backend API
4. Public select karein
5. **README, .gitignore mat add karein** (code already hai)
6. Create repository click karein

## 2. Remote update + Push
Repo create hone ke baad, apna GitHub **username** use karein:

```bash
cd /Applications/XAMPP/xamppfiles/htdocs/propert_paython/backend-new
git remote set-url origin https://github.com/YOUR_USERNAME/LGP-backend.git
git push -u origin main
```

Agar `navsupport` aapka GitHub username hai to:
```bash
git remote set-url origin https://github.com/navsupport/LGP-backend.git
git push -u origin main
```

## 3. Done

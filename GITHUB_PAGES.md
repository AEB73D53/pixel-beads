# 部署到 GitHub Pages（上线官网 + 在线工具）

网站源码在 `site/`（纯静态：`index.html` 官网 + `tool.html` 在线工具 + `gallery.html` 灵感库）。
`dist/拼豆助手.exe`（79MB）**不推仓库**，走 GitHub Releases 当下载资源。

已内置 `.github/workflows/pages.yml`：每次推 `site/**` 到 `main` 自动发布 Pages。

---

## 一、创建仓库并推送（一次性）

在 GitHub 网页创建新仓库（建议 Public，勾选 Add README 可不用，任意名字），然后：

```bash
cd "C:\Users\Lv Yizhou\Desktop\pindu-tool"

# 1) 关联你的远程仓库（把 <你的名字>/<仓库名> 换成实际的）
git remote add origin https://github.com/<你的名字>/<仓库名>.git

# 2) 首次提交（dist、灵感采集图已被 .gitignore 排除）
git add .
git commit -m "v2.0：拼豆助手 桌面端 + 官网/在线工具"
git push -u origin main
```

> 在仓库 Settings → Pages ：
> - **Build and deployment → Source** 选 **「GitHub Actions」**（用仓库内的 workflow，不选 "Deploy from a branch"）。
> - 第一次 push 后 Actions 会自动跑，完成后页面地址显示为 `https://<你的名字>.github.io/<仓库名>/`。

## 二、发布桌面版 exe（下载按钮指向这里）

79MB 的 exe 用 **Releases** 托管（GitHub 单文件上限 100MB，正好可放）：

```bash
cd "C:\Users\Lv Yizhou\Desktop\pindu-tool"
git tag v2.0
git push origin v2.0
gh release create v2.0 dist/拼豆助手.exe --title "拼豆助手 v2.0 · 桌面版" \
  --notes "照片→拼豆图纸（离线抠图/色卡映射/编号图纸/耗材清单/灵感库）。支持 PDF / Excel 导出。"
```

发布后把 `site/index.html` 里下载按钮的真实地址替换为：

```
https://github.com/<你的名字>/<仓库名>/releases/download/v2.0/拼豆助手.exe
```

## 三、日常更新网站

- 改 `site/**` 里的内容 → `git add . && git commit -m "..." && git push` → Actions 自动重新发布。
- 本地预览：`cd site && python -m http.server 8000`，浏览器打开 `http://localhost:8000`。

## 四、其他说明

- 页面无任何后端：在线工具全部在浏览器本地计算，不上传图片。
- 灵感采集图含原作者版权，已从仓库排除（仅本地使用）。
- 想自定义域名（如 `pindu.example.com`）：仓库 Settings → Pages → Custom domain，并在 DNS 加 CNAME。
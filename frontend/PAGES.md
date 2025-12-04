# 台灣水文網絡圖 - 頁面說明

## 🎯 兩個獨立頁面

### 1. 原始版本
- **URL**: `http://localhost:5173/` 或 `http://localhost:5173/index.html`
- **檔案**: `index.html` → `src/main.js` → `src/App.vue`
- **說明**: 原始的 index 頁面（不會被覆蓋）

### 2. 增強版本 ✨
- **URL**: `http://localhost:5173/enhanced.html`
- **檔案**: `enhanced.html` → `src/enhanced.js` → `src/EnhancedApp.vue`
- **功能**:
  - 右側控制面板
  - 點擊高亮關聯
  - 更好的互動體驗

---

## 🚀 使用方式

### 開發模式
```bash
npm run dev
```

訪問:
- 原始版: http://localhost:5173/
- 增強版: http://localhost:5173/enhanced.html

### 建置
```bash
npm run build
```

會產生兩個獨立的 HTML 檔案在 `dist/` 資料夾

---

## 📁 檔案結構

```
frontend/
├── index.html          # 原始版入口
├── enhanced.html       # 增強版入口（獨立）
├── src/
│   ├── main.js        # 原始版 JS 入口
│   ├── enhanced.js    # 增強版 JS 入口（獨立）
│   ├── App.vue        # 原始版根組件
│   ├── EnhancedApp.vue# 增強版根組件（獨立）
│   └── components/
│       ├── HydroGraph.vue         # 原始組件
│       └── HydroGraphEnhanced.vue # 增強組件
```

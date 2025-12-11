# getStationsByRiver vs getStationsByWaterSystem 差異說明

## 核心差異

| 工具 | 查詢範圍 | 範例數量 |
|------|---------|---------|
| `getStationsByRiver("蘭陽溪")` | 只查「蘭陽溪」這條河上的測站 | 12 站 |
| `getStationsByWaterSystem("蘭陽溪")` | 查「蘭陽溪水系」內所有河川上的測站 | 22 站 |

## 圖解說明

```
蘭陽溪水系結構：
┌─────────────────────────────────────────────────────┐
│  蘭陽溪水系                                          │
│  ┌───────────────────────────────────────────────┐  │
│  │ 蘭陽溪（主流）          ← getStationsByRiver   │  │
│  │ 12 個測站                                      │  │
│  └───────────────────────────────────────────────┘  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │ 宜蘭河      │ │ 羅東溪      │ │ 清水溪      │   │
│  │ (支流)      │ │ (支流)      │ │ (支流)      │   │
│  └─────────────┘ └─────────────┘ └─────────────┘   │
│  ┌─────────────┐ ┌─────────────┐                   │
│  │ 打狗溪      │ │ 其他支流... │                   │
│  │ (支流)      │ │             │                   │
│  └─────────────┘ └─────────────┘                   │
│                                                     │
│  ↑ getStationsByWaterSystem 查詢整個水系 = 22 站    │
└─────────────────────────────────────────────────────┘
```

## 簡單記憶

```
getStationsByRiver("蘭陽溪")      → 只有主流上的 12 站
getStationsByWaterSystem("蘭陽溪") → 主流 + 所有支流 = 22 站
```

## 使用情境

- **想知道單一河川的測站** → 使用 `getStationsByRiver`
- **想知道整個流域的測站** → 使用 `getStationsByWaterSystem`

## 技術實現差異

### getStationsByRiver
```cypher
MATCH (s:Station)-[:LOCATED_ON]->(r:River {name: $riverName})
-- 只匹配該河川上的測站
```

### getStationsByWaterSystem
```cypher
MATCH (s:Station)-[:LOCATED_ON]->(r:River)-[:BELONGS_TO]->(ws:WaterSystem)
WHERE ws.name = $waterSystemName
-- 匹配水系內所有河川上的測站
```

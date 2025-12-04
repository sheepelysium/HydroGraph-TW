export const mockData = {
    nodes: [
        // Water Systems
        { id: "WS1", name: "淡水河水系", group: "WaterSystem", radius: 30 },

        // Rivers
        { id: "R1", name: "淡水河", group: "River", radius: 20 },
        { id: "R2", name: "基隆河", group: "River", radius: 15 },
        { id: "R3", name: "大漢溪", group: "River", radius: 15 },
        { id: "R4", name: "新店溪", group: "River", radius: 15 },

        // Basins
        { id: "B1", name: "臺北流域", group: "Basin", radius: 25 },

        // Watersheds
        { id: "W1", name: "基隆集水區", group: "Watershed", radius: 10 },
        { id: "W2", name: "大漢溪集水區", group: "Watershed", radius: 10 },

        // Stations
        { id: "S1", name: "測站 A", group: "Station", radius: 5 },
        { id: "S2", name: "測站 B", group: "Station", radius: 5 },
    ],
    links: [
        // BELONGS_TO 是分類關係，不畫箭頭（避免與水流方向混淆）
        // 透過節點顏色和右側列表就能知道分類

        // FLOWS_INTO: 支流 -> 主流（實際水流方向）
        { source: "R2", target: "R1", type: "FLOWS_INTO" },  // 基隆河 → 淡水河
        { source: "R3", target: "R1", type: "FLOWS_INTO" },  // 大漢溪 → 淡水河
        { source: "R4", target: "R1", type: "FLOWS_INTO" },  // 新店溪 → 淡水河

        // DRAINS_TO: Watershed -> River
        { source: "W1", target: "R2", type: "DRAINS_TO" },
        { source: "W2", target: "R3", type: "DRAINS_TO" },

        // PART_OF: Watershed -> Basin
        { source: "W1", target: "B1", type: "PART_OF" },
        { source: "W2", target: "B1", type: "PART_OF" },

        // LOCATED_ON: Station -> River
        { source: "S1", target: "R1", type: "LOCATED_ON" },
        { source: "S2", target: "R2", type: "LOCATED_ON" },
    ]
};

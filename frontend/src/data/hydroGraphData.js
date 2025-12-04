export const hydroGraphData = {
  nodes: [
    // Water systems (台灣主要水系 - 依地理位置北到南、西到東)
    { id: 'WS_DANSHUI', name: '淡水河水系', group: 'WaterSystem', radius: 32, region: '北北基主要供水', lat: 25.08, lon: 121.45 },
    { id: 'WS_LANYANG', name: '蘭陽溪水系', group: 'WaterSystem', radius: 28, region: '宜蘭主要水源', lat: 24.70, lon: 121.75 },
    { id: 'WS_DAJIA', name: '大甲溪水系', group: 'WaterSystem', radius: 28, region: '中部水力發電', lat: 24.35, lon: 120.95 },
    { id: 'WS_ZHUOSHUI', name: '濁水溪水系', group: 'WaterSystem', radius: 30, region: '中南部灌溉', lat: 23.82, lon: 120.50 },
    { id: 'WS_ZENGWEN', name: '曾文溪水系', group: 'WaterSystem', radius: 28, region: '嘉南灌溉核心', lat: 23.17, lon: 120.52 },
    { id: 'WS_GAOPING', name: '高屏溪水系', group: 'WaterSystem', radius: 30, region: '高屏南科供水', lat: 22.65, lon: 120.53 },
    { id: 'WS_XIUGULUAN', name: '秀姑巒溪水系', group: 'WaterSystem', radius: 26, region: '東部主要河川', lat: 23.48, lon: 121.40 },
    { id: 'WS_BEINAN', name: '卑南溪水系', group: 'WaterSystem', radius: 26, region: '台東水源', lat: 22.85, lon: 121.10 },

    // Rivers (主要河川)
    // 淡水河水系
    { id: 'R_DANSHUI', name: '淡水河', group: 'River', radius: 24, flow: '主幹河川', lat: 25.12, lon: 121.44 },
    { id: 'R_DAHAN', name: '大漢溪', group: 'River', radius: 19, flow: '支流匯入', lat: 24.90, lon: 121.30 },
    { id: 'R_XINDIAN', name: '新店溪', group: 'River', radius: 18, flow: '支流匯入', lat: 24.96, lon: 121.55 },
    { id: 'R_JILONG', name: '基隆河', group: 'River', radius: 18, flow: '支流匯入', lat: 25.08, lon: 121.62 },
    // 蘭陽溪水系
    { id: 'R_LANYANG', name: '蘭陽溪', group: 'River', radius: 22, flow: '東北主幹', lat: 24.70, lon: 121.75 },
    // 大甲溪水系
    { id: 'R_DAJIA', name: '大甲溪', group: 'River', radius: 22, flow: '中部主幹', lat: 24.35, lon: 120.95 },
    // 濁水溪水系
    { id: 'R_ZHUOSHUI', name: '濁水溪', group: 'River', radius: 24, flow: '最長河川', lat: 23.82, lon: 120.50 },
    // 曾文溪水系
    { id: 'R_ZENGWEN', name: '曾文溪', group: 'River', radius: 22, flow: '南部主幹', lat: 23.25, lon: 120.63 },
    // 高屏溪水系
    { id: 'R_GAOPING', name: '高屏溪', group: 'River', radius: 24, flow: '流量最大', lat: 22.65, lon: 120.53 },
    { id: 'R_LAONONG', name: '荖濃溪', group: 'River', radius: 17, flow: '支流匯入', lat: 22.88, lon: 120.73 },
    // 秀姑巒溪水系
    { id: 'R_XIUGULUAN', name: '秀姑巒溪', group: 'River', radius: 22, flow: '東部主幹', lat: 23.48, lon: 121.40 },
    // 卑南溪水系
    { id: 'R_BEINAN', name: '卑南溪', group: 'River', radius: 20, flow: '台東主流', lat: 22.85, lon: 121.10 },

    // Watersheds
    { id: 'W_DAHAN', name: '大漢溪集水區', group: 'Watershed', radius: 13, lat: 24.77, lon: 121.25 },
    { id: 'W_XINDIAN', name: '新店溪集水區', group: 'Watershed', radius: 12, lat: 24.90, lon: 121.60 },
    { id: 'W_JILONG', name: '基隆河集水區', group: 'Watershed', radius: 12, lat: 25.15, lon: 121.60 },
    { id: 'W_ZENGWEN', name: '曾文溪集水區', group: 'Watershed', radius: 13, lat: 23.21, lon: 120.60 },
    { id: 'W_LAONONG', name: '荖濃溪集水區', group: 'Watershed', radius: 12, lat: 22.92, lon: 120.70 },
    { id: 'W_GAOPING', name: '高屏溪集水區', group: 'Watershed', radius: 12, lat: 22.62, lon: 120.58 },

    // Basins
    { id: 'B_NORTH', name: '北部流域', group: 'Basin', radius: 18, lat: 24.90, lon: 121.35 },
    { id: 'B_SOUTH', name: '南部流域', group: 'Basin', radius: 18, lat: 23.00, lon: 120.60 },
    { id: 'B_COAST', name: '沿海流域', group: 'Basin', radius: 14, lat: 22.80, lon: 120.25 },

    // Stations
    { id: 'S_GUANDU', name: '關渡站', group: 'Station', radius: 7, lat: 25.12, lon: 121.45 },
    { id: 'S_SANXIA', name: '三峽大橋站', group: 'Station', radius: 7, lat: 24.93, lon: 121.38 },
    { id: 'S_FEITSUI', name: '翡翠水庫站', group: 'Station', radius: 7, lat: 24.93, lon: 121.66 },
    { id: 'S_NEIHU', name: '內湖站', group: 'Station', radius: 7, lat: 25.08, lon: 121.60 },
    { id: 'S_ZENGWEN', name: '曾文壩站', group: 'Station', radius: 7, lat: 23.20, lon: 120.53 },
    { id: 'S_NANHUA', name: '南化水庫站', group: 'Station', radius: 7, lat: 23.07, lon: 120.48 },
    { id: 'S_PINGTUNG', name: '屏東潮州站', group: 'Station', radius: 7, lat: 22.67, lon: 120.49 },
    { id: 'S_LAONONG', name: '荖濃溪林園站', group: 'Station', radius: 7, lat: 22.85, lon: 120.63 },
  ],
  links: [
    // River to Water system (河川歸屬水系)
    { source: 'R_DANSHUI', target: 'WS_DANSHUI', type: 'BELONGS_TO', weight: 5 },
    { source: 'R_LANYANG', target: 'WS_LANYANG', type: 'BELONGS_TO', weight: 5 },
    { source: 'R_DAJIA', target: 'WS_DAJIA', type: 'BELONGS_TO', weight: 5 },
    { source: 'R_ZHUOSHUI', target: 'WS_ZHUOSHUI', type: 'BELONGS_TO', weight: 5 },
    { source: 'R_ZENGWEN', target: 'WS_ZENGWEN', type: 'BELONGS_TO', weight: 5 },
    { source: 'R_GAOPING', target: 'WS_GAOPING', type: 'BELONGS_TO', weight: 5 },
    { source: 'R_XIUGULUAN', target: 'WS_XIUGULUAN', type: 'BELONGS_TO', weight: 5 },
    { source: 'R_BEINAN', target: 'WS_BEINAN', type: 'BELONGS_TO', weight: 5 },

    // Tributaries to main rivers (支流匯入主流)
    { source: 'R_DAHAN', target: 'R_DANSHUI', type: 'TRIBUTARY_TO', weight: 4 },
    { source: 'R_XINDIAN', target: 'R_DANSHUI', type: 'TRIBUTARY_TO', weight: 3 },
    { source: 'R_JILONG', target: 'R_DANSHUI', type: 'TRIBUTARY_TO', weight: 3 },
    { source: 'R_LAONONG', target: 'R_GAOPING', type: 'TRIBUTARY_TO', weight: 4 },

    // Watersheds draining to rivers
    { source: 'W_DAHAN', target: 'R_DAHAN', type: 'DRAINS_TO', weight: 3 },
    { source: 'W_XINDIAN', target: 'R_XINDIAN', type: 'DRAINS_TO', weight: 3 },
    { source: 'W_JILONG', target: 'R_JILONG', type: 'DRAINS_TO', weight: 3 },
    { source: 'W_ZENGWEN', target: 'R_ZENGWEN', type: 'DRAINS_TO', weight: 3 },
    { source: 'W_LAONONG', target: 'R_LAONONG', type: 'DRAINS_TO', weight: 3 },
    { source: 'W_GAOPING', target: 'R_GAOPING', type: 'DRAINS_TO', weight: 3 },

    // Watersheds to basins
    { source: 'W_DAHAN', target: 'B_NORTH', type: 'PART_OF', weight: 2 },
    { source: 'W_XINDIAN', target: 'B_NORTH', type: 'PART_OF', weight: 2 },
    { source: 'W_JILONG', target: 'B_NORTH', type: 'PART_OF', weight: 2 },
    { source: 'W_ZENGWEN', target: 'B_SOUTH', type: 'PART_OF', weight: 2 },
    { source: 'W_LAONONG', target: 'B_SOUTH', type: 'PART_OF', weight: 2 },
    { source: 'W_GAOPING', target: 'B_SOUTH', type: 'PART_OF', weight: 2 },

    // Stations on rivers
    { source: 'S_GUANDU', target: 'R_DANSHUI', type: 'GAUGES', weight: 1 },
    { source: 'S_SANXIA', target: 'R_DAHAN', type: 'GAUGES', weight: 1 },
    { source: 'S_FEITSUI', target: 'R_XINDIAN', type: 'GAUGES', weight: 1 },
    { source: 'S_NEIHU', target: 'R_JILONG', type: 'GAUGES', weight: 1 },
    { source: 'S_ZENGWEN', target: 'R_ZENGWEN', type: 'GAUGES', weight: 1 },
    { source: 'S_NANHUA', target: 'R_ZENGWEN', type: 'GAUGES', weight: 1 },
    { source: 'S_PINGTUNG', target: 'R_GAOPING', type: 'GAUGES', weight: 1 },
    { source: 'S_LAONONG', target: 'R_LAONONG', type: 'GAUGES', weight: 1 },

    // Basin support back to systems (for highlighting cross layer)
    { source: 'B_NORTH', target: 'WS_DANSHUI', type: 'FEEDS', weight: 2 },
    { source: 'B_SOUTH', target: 'WS_GAOPING', type: 'FEEDS', weight: 2 },
    { source: 'B_SOUTH', target: 'WS_ZENGWEN', type: 'FEEDS', weight: 1 },
  ],
};

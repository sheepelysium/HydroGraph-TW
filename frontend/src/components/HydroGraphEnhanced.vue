<template>
  <div class="w-full h-full bg-gray-900 flex relative overflow-hidden">
    <!-- 左側：圖表區域 -->
    <div class="flex-1 relative" ref="container">
      <svg ref="svg" class="w-full h-full cursor-move"></svg>

      <!-- 圖例 -->
      <div class="absolute top-4 left-4 z-10 bg-gray-800/90 backdrop-blur p-3 rounded-lg border border-gray-700 shadow-xl">
        <h3 class="text-sm font-bold text-blue-400 mb-2">圖例</h3>
        <div class="space-y-1 text-xs text-gray-300">
          <div class="flex items-center gap-2">
            <span class="w-3 h-3 rounded-full bg-blue-500"></span> 水系
          </div>
          <div class="flex items-center gap-2">
            <span class="w-3 h-3 rounded-full bg-cyan-500"></span> 河流
          </div>
          <div class="flex items-center gap-2">
            <span class="w-3 h-3 rounded-full bg-teal-500"></span> 集水區
          </div>
          <div class="flex items-center gap-2">
            <span class="w-3 h-3 rounded-full bg-violet-500"></span> 流域
          </div>
          <div class="flex items-center gap-2">
            <span class="w-3 h-3 rounded-full bg-fuchsia-500"></span> 測站
          </div>
        </div>
      </div>

      <!-- Tooltip -->
      <div v-if="hoveredNode"
           class="absolute pointer-events-none bg-gray-900/95 text-white p-3 rounded-lg border border-blue-500/50 shadow-2xl z-20"
           :style="{ left: tooltipX + 'px', top: tooltipY + 'px' }">
        <div class="font-bold text-base">{{ hoveredNode.name }}</div>
        <div class="text-xs text-gray-400 mt-1">{{ groupNameMap[hoveredNode.group] }}</div>
      </div>
    </div>

    <!-- 右側：控制面板 -->
    <div class="w-80 bg-gray-800 border-l border-gray-700 overflow-y-auto flex-shrink-0">
      <!-- 標題 -->
      <div class="sticky top-0 bg-gray-800 border-b border-gray-700 p-4 z-10">
        <h2 class="text-xl font-bold text-blue-400">台灣水文網絡圖</h2>
        <p class="text-xs text-gray-400 mt-1">點擊項目以高亮顯示</p>
      </div>

      <!-- 水系資訊 -->
      <div class="p-4 border-b border-gray-700">
        <h3 class="text-sm font-bold text-gray-300 mb-2">🌊 水系資訊</h3>
        <div class="space-y-2">
          <div
            v-for="ws in waterSystems"
            :key="ws.id"
            @click="highlightNode(ws.id)"
            :class="['p-2 rounded cursor-pointer transition-colors',
                     selectedNodeId === ws.id ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600']">
            <div class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full bg-blue-500"></span>
              <span class="text-sm text-white font-medium">{{ ws.name }}</span>
            </div>
            <div class="text-xs text-gray-400 mt-1 ml-5">
              包含 {{ getRiverCount(ws.id) }} 條河川
            </div>
          </div>
        </div>
      </div>

      <!-- 河川列表 -->
      <div class="p-4 border-b border-gray-700">
        <h3 class="text-sm font-bold text-gray-300 mb-2">🏞️ 主要河川</h3>
        <div class="space-y-2">
          <div
            v-for="river in rivers"
            :key="river.id"
            @click="highlightNode(river.id)"
            :class="['p-2 rounded cursor-pointer transition-colors',
                     selectedNodeId === river.id ? 'bg-cyan-600' : 'bg-gray-700 hover:bg-gray-600']">
            <div class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full bg-cyan-500"></span>
              <span class="text-sm text-white">{{ river.name }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 集水區 -->
      <div class="p-4 border-b border-gray-700">
        <h3 class="text-sm font-bold text-gray-300 mb-2">💧 集水區</h3>
        <div class="space-y-2">
          <div
            v-for="ws in watersheds"
            :key="ws.id"
            @click="highlightNode(ws.id)"
            :class="['p-2 rounded cursor-pointer transition-colors',
                     selectedNodeId === ws.id ? 'bg-teal-600' : 'bg-gray-700 hover:bg-gray-600']">
            <div class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full bg-teal-500"></span>
              <span class="text-sm text-white">{{ ws.name }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 測站 -->
      <div class="p-4 border-b border-gray-700">
        <h3 class="text-sm font-bold text-gray-300 mb-2">📍 測站</h3>
        <div class="space-y-2">
          <div
            v-for="station in stations"
            :key="station.id"
            @click="highlightNode(station.id)"
            :class="['p-2 rounded cursor-pointer transition-colors',
                     selectedNodeId === station.id ? 'bg-fuchsia-600' : 'bg-gray-700 hover:bg-gray-600']">
            <div class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full bg-fuchsia-500"></span>
              <span class="text-sm text-white">{{ station.name }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 流域 -->
      <div class="p-4">
        <h3 class="text-sm font-bold text-gray-300 mb-2">🗺️ 流域</h3>
        <div class="space-y-2">
          <div
            v-for="basin in basins"
            :key="basin.id"
            @click="highlightNode(basin.id)"
            :class="['p-2 rounded cursor-pointer transition-colors',
                     selectedNodeId === basin.id ? 'bg-violet-600' : 'bg-gray-700 hover:bg-gray-600']">
            <div class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full bg-violet-500"></span>
              <span class="text-sm text-white">{{ basin.name }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, computed, onUnmounted } from 'vue';
import * as d3 from 'd3';
import { mockData } from '../data/mockData';

const container = ref(null);
const svg = ref(null);
const hoveredNode = ref(null);
const tooltipX = ref(0);
const tooltipY = ref(0);
const selectedNodeId = ref(null);

let simulation = null;
let nodeElements = null;
let linkElements = null;

const colorMap = {
  WaterSystem: '#3b82f6',
  River: '#06b6d4',
  Watershed: '#14b8a6',
  Basin: '#8b5cf6',
  Station: '#d946ef'
};

const groupNameMap = {
  WaterSystem: '水系',
  River: '河流',
  Watershed: '集水區',
  Basin: '流域',
  Station: '測站'
};

// 分類節點
const waterSystems = computed(() => mockData.nodes.filter(n => n.group === 'WaterSystem'));
const rivers = computed(() => mockData.nodes.filter(n => n.group === 'River'));
const watersheds = computed(() => mockData.nodes.filter(n => n.group === 'Watershed'));
const basins = computed(() => mockData.nodes.filter(n => n.group === 'Basin'));
const stations = computed(() => mockData.nodes.filter(n => n.group === 'Station'));

// 計算河川數量（改為計算流入主流的支流數）
const getRiverCount = (waterSystemId) => {
  // 簡化：淡水河水系固定顯示 4 條河川（1主流+3支流）
  return 4;
};

// 高亮節點及其關聯
const highlightNode = (nodeId) => {
  selectedNodeId.value = nodeId;

  if (!nodeElements || !linkElements) return;

  // 找出所有相關的連結
  const relatedLinks = mockData.links.filter(l =>
    l.source === nodeId || l.target === nodeId ||
    (typeof l.source === 'object' && l.source.id === nodeId) ||
    (typeof l.target === 'object' && l.target.id === nodeId)
  );

  // 找出所有相關的節點
  const relatedNodeIds = new Set([nodeId]);
  relatedLinks.forEach(l => {
    const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
    const targetId = typeof l.target === 'object' ? l.target.id : l.target;
    relatedNodeIds.add(sourceId);
    relatedNodeIds.add(targetId);
  });

  // 更新節點樣式
  nodeElements
    .attr('opacity', d => relatedNodeIds.has(d.id) ? 1 : 0.15)
    .attr('stroke-width', d => d.id === nodeId ? 4 : 1.5)
    .attr('stroke', d => d.id === nodeId ? '#fbbf24' : '#fff');

  // 更新連結樣式
  linkElements
    .attr('opacity', l => {
      const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
      const targetId = typeof l.target === 'object' ? l.target.id : l.target;
      return (sourceId === nodeId || targetId === nodeId) ? 1 : 0.1;
    })
    .attr('stroke-width', l => {
      const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
      const targetId = typeof l.target === 'object' ? l.target.id : l.target;
      return (sourceId === nodeId || targetId === nodeId) ? 3 : 1.5;
    })
    .attr('stroke', l => {
      const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
      const targetId = typeof l.target === 'object' ? l.target.id : l.target;
      return (sourceId === nodeId || targetId === nodeId) ? '#60a5fa' : '#4b5563';
    });
};

// 重置高亮
const resetHighlight = () => {
  selectedNodeId.value = null;

  if (!nodeElements || !linkElements) return;

  nodeElements
    .attr('opacity', 1)
    .attr('stroke-width', 1.5)
    .attr('stroke', '#fff');

  linkElements
    .attr('opacity', 0.6)
    .attr('stroke-width', 1.5)
    .attr('stroke', '#4b5563');
};

onMounted(() => {
  if (!container.value || !svg.value) return;

  const nodes = JSON.parse(JSON.stringify(mockData.nodes));
  const links = JSON.parse(JSON.stringify(mockData.links));

  const svgEl = d3.select(svg.value);
  const g = svgEl.append("g");

  const rect = container.value.getBoundingClientRect();
  const width = rect.width;
  const height = rect.height;

  svgEl.attr("viewBox", [0, 0, width, height]);

  const zoom = d3.zoom()
    .scaleExtent([0.1, 4])
    .on("zoom", (event) => {
      g.attr("transform", event.transform);
    });

  svgEl.call(zoom);

  // 雙擊背景重置高亮
  svgEl.on("dblclick.zoom", null).on("dblclick", resetHighlight);

  simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(d => d.id).distance(150))
    .force("charge", d3.forceManyBody().strength(-800))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collide", d3.forceCollide().radius(d => d.radius + 30));

  // 箭頭標記
  svgEl.append("defs").append("marker")
    .attr("id", "arrow")
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 25)
    .attr("refY", 0)
    .attr("markerWidth", 6)
    .attr("markerHeight", 6)
    .attr("orient", "auto")
    .append("path")
    .attr("fill", "#4b5563")
    .attr("d", "M0,-5L10,0L0,5");

  // 繪製台灣地圖 (SVG)
  const mapGroup = g.append("g")
    .attr("class", "map-layer");

  d3.xml("/src/data/taiwan.svg").then(data => {
    const importedNode = document.importNode(data.documentElement, true);
    const mapSvg = mapGroup.node().appendChild(importedNode);
    
    // 調整 SVG 大小和位置以適應畫面
    const d3Map = d3.select(mapSvg);
    d3Map.attr("width", width)
         .attr("height", height)
         .attr("preserveAspectRatio", "xMidYMid meet")
         .style("opacity", 0.3) // 降低不透明度作為背景
         .style("pointer-events", "none"); // 確保不影響滑鼠互動
         
    // 如果 SVG 內部有 fill 設定，覆蓋為深色主題
    d3Map.selectAll("path")
         .attr("fill", "#1e293b")
         .attr("stroke", "#334155")
         .attr("stroke-width", 1);
  });

  linkElements = g.append("g")
    .attr("stroke", "#4b5563")
    .attr("stroke-opacity", 0.6)
    .selectAll("line")
    .data(links)
    .join("line")
    .attr("stroke-width", 1.5)
    .attr("marker-end", "url(#arrow)");

  nodeElements = g.append("g")
    .attr("stroke", "#fff")
    .attr("stroke-width", 1.5)
    .selectAll("circle")
    .data(nodes)
    .join("circle")
    .attr("r", d => d.radius)
    .attr("fill", d => colorMap[d.group] || '#9ca3af')
    .call(drag(simulation))
    .on("click", (event, d) => {
      event.stopPropagation();
      highlightNode(d.id);
    });

  const labels = g.append("g")
    .attr("class", "labels")
    .selectAll("text")
    .data(nodes)
    .join("text")
    .attr("dx", 12)
    .attr("dy", ".35em")
    .text(d => d.name)
    .attr("fill", "#e5e7eb")
    .style("font-size", "11px")
    .style("pointer-events", "none")
    .style("opacity", 0.9);

  nodeElements
    .on("mouseover", (event, d) => {
      hoveredNode.value = d;
      tooltipX.value = event.pageX + 10;
      tooltipY.value = event.pageY + 10;
      d3.select(event.currentTarget).attr("stroke", "#60a5fa").attr("stroke-width", 3);
    })
    .on("mousemove", (event) => {
      tooltipX.value = event.pageX + 10;
      tooltipY.value = event.pageY + 10;
    })
    .on("mouseout", (event, d) => {
      hoveredNode.value = null;
      const strokeWidth = d.id === selectedNodeId.value ? 4 : 1.5;
      const strokeColor = d.id === selectedNodeId.value ? '#fbbf24' : '#fff';
      d3.select(event.currentTarget).attr("stroke", strokeColor).attr("stroke-width", strokeWidth);
    });

  simulation.on("tick", () => {
    linkElements
      .attr("x1", d => d.source.x)
      .attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x)
      .attr("y2", d => d.target.y);

    nodeElements
      .attr("cx", d => d.x)
      .attr("cy", d => d.y);

    labels
      .attr("x", d => d.x)
      .attr("y", d => d.y);
  });

  const resizeObserver = new ResizeObserver(entries => {
    for (const entry of entries) {
      const { width, height } = entry.contentRect;
      svgEl.attr("viewBox", [0, 0, width, height]);
      simulation.force("center", d3.forceCenter(width / 2, height / 2));
      simulation.alpha(0.3).restart();
      
      // SVG 背景會自動適應 viewBox，無需額外 JS 更新
    }
  });

  resizeObserver.observe(container.value);

  onUnmounted(() => {
    resizeObserver.disconnect();
    simulation.stop();
  });
});

function drag(simulation) {
  function dragstarted(event) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    event.subject.fx = event.subject.x;
    event.subject.fy = event.subject.y;
  }

  function dragged(event) {
    event.subject.fx = event.x;
    event.subject.fy = event.y;
  }

  function dragended(event) {
    if (!event.active) simulation.alphaTarget(0);
    event.subject.fx = null;
    event.subject.fy = null;
  }

  return d3.drag()
    .on("start", dragstarted)
    .on("drag", dragged)
    .on("end", dragended);
}
</script>

<style scoped>
/* 自訂滾動條 */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: #1f2937;
}

::-webkit-scrollbar-thumb {
  background: #4b5563;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #6b7280;
}
</style>

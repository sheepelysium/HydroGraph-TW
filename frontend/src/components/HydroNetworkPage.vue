<template>
  <div class="min-h-screen w-full flex bg-slate-950 text-slate-50 relative overflow-hidden">
    <div class="absolute inset-0 bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900"></div>
    <div class="absolute inset-0 pointer-events-none">
      <div class="absolute -left-32 -top-24 w-96 h-96 bg-sky-500/10 rounded-full blur-3xl"></div>
      <div class="absolute right-10 top-20 w-64 h-64 bg-fuchsia-500/10 rounded-full blur-3xl"></div>
      <div class="absolute -bottom-24 left-32 w-80 h-80 bg-emerald-400/10 rounded-full blur-3xl"></div>
    </div>

    <!-- Graph area -->
    <div class="flex-1 relative" ref="container">
      <svg ref="svg" class="w-full h-full relative z-10"></svg>

      <!-- Legend -->
      <div class="absolute top-6 left-6 z-20 bg-slate-900/80 backdrop-blur-lg border border-slate-800 rounded-2xl p-4 shadow-2xl">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs uppercase tracking-[0.2em] text-slate-400">Layers</p>
            <h3 class="text-lg font-semibold text-slate-50 mt-1">台灣水文層級</h3>
          </div>
          <div class="flex gap-2">
            <button
              class="text-xs px-3 py-1 rounded-full bg-slate-800 text-slate-200 border border-slate-700 hover:border-sky-400 transition"
              @click="fitToScreen"
            >
              適應視圖
            </button>
            <button
              class="text-xs px-3 py-1 rounded-full bg-slate-800 text-slate-200 border border-slate-700 hover:border-sky-400 transition"
              @click="resetView"
            >
              重置聚焦
            </button>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3 mt-3 text-xs text-slate-200">
          <div v-for="(meta, key) in groupMeta" :key="key" class="flex items-center gap-2">
            <span class="w-3 h-3 rounded-full" :style="{ background: meta.color }"></span>
            <div>
              <div class="font-semibold">{{ meta.label }}</div>
              <div class="text-[11px] text-slate-400">{{ meta.caption }}</div>
            </div>
          </div>
        </div>
        <div class="border-t border-slate-800 mt-3 pt-3">
          <p class="text-[11px] uppercase tracking-[0.2em] text-slate-400 mb-2">Edge Types</p>
          <div class="grid grid-cols-2 gap-2">
            <div
              v-for="(meta, key) in linkMeta"
              :key="key"
              class="flex items-center gap-2 text-[11px] text-slate-300"
            >
              <span class="h-0.5 w-6 rounded-full" :style="{ background: meta.color }"></span>
              <span>{{ meta.label }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Hover tooltip -->
      <div
        v-if="hoveredNode"
        class="absolute z-30 bg-slate-900/95 border border-sky-500/40 rounded-xl px-3 py-2 shadow-2xl text-sm"
        :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }"
      >
        <div class="flex items-center gap-2">
          <span
            class="w-2.5 h-2.5 rounded-full"
            :style="{ background: groupMeta[hoveredNode.group]?.color || '#94a3b8' }"
          ></span>
          <div class="font-semibold text-slate-50">{{ hoveredNode.name }}</div>
        </div>
        <div class="text-[11px] text-slate-400 mt-1">
          {{ groupMeta[hoveredNode.group]?.label || '節點' }}
        </div>
      </div>
    </div>

    <!-- Sidebar -->
    <aside class="w-[380px] max-w-md h-screen bg-slate-900/85 border-l border-slate-800 backdrop-blur-xl relative z-20 flex flex-col">
      <div class="p-6 border-b border-slate-800">
        <p class="text-xs uppercase tracking-[0.25em] text-slate-400">Hydro Atlas</p>
        <h1 class="text-2xl font-semibold text-slate-50 mt-2 leading-tight">台灣水文關係導覽</h1>
        <p class="text-sm text-slate-400 mt-2">
          參考政治獻金的互動方式，改編成水系—河川—集水區—流域—測站的互動關係圖。
          點擊右側列表或圖上節點，會高亮該層級的相關路徑。
        </p>
        <div class="flex items-center gap-2 mt-4">
          <input
            v-model.trim="searchTerm"
            @keyup.enter="applySearch"
            type="text"
            placeholder="搜尋水系 / 河川 / 測站"
            class="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-sky-400 focus:outline-none"
          />
          <button
            class="px-3 py-2 text-xs font-semibold rounded-lg bg-sky-500 text-white hover:bg-sky-400 transition"
            @click="applySearch"
          >
            GO
          </button>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto custom-scroll">
        <section class="p-6 border-b border-slate-800">
          <div class="flex items-center justify-between">
            <div class="text-xs uppercase tracking-[0.2em] text-slate-400">Focus</div>
            <button
              class="text-[11px] text-slate-400 underline decoration-slate-600 hover:text-sky-300"
              @click="resetView"
            >
              解除聚焦
            </button>
          </div>

          <div v-if="activeNode" class="mt-3 bg-slate-800/60 rounded-xl border border-slate-700 p-4">
            <div class="flex items-start justify-between">
              <div>
                <p class="text-xs text-slate-400">{{ groupMeta[activeNode.group]?.label || '節點' }}</p>
                <h3 class="text-xl font-semibold text-slate-50 mt-1">{{ activeNode.name }}</h3>
                <p class="text-sm text-slate-400 mt-1">
                  {{ activeNode.region || activeNode.flow || '相關路徑已高亮' }}
                </p>
              </div>
              <div
                class="w-10 h-10 rounded-full border-2 flex items-center justify-center text-xs font-bold"
                :style="{ borderColor: groupMeta[activeNode.group]?.color || '#94a3b8', color: groupMeta[activeNode.group]?.color || '#94a3b8' }"
              >
                {{ groupMeta[activeNode.group]?.short || 'N' }}
              </div>
            </div>

            <!-- 測站詳細資訊 -->
            <div v-if="activeNode.group === 'WaterStation' || activeNode.group === 'RainStation'" class="mt-3 space-y-2 text-xs">
              <div class="flex items-center justify-between py-1.5 border-b border-slate-700/50">
                <span class="text-slate-400">測站代碼</span>
                <span class="text-slate-50 font-mono">{{ activeNode.id.replace('S_', '') }}</span>
              </div>
              <div v-if="activeNode.lat && activeNode.lon" class="flex items-center justify-between py-1.5 border-b border-slate-700/50">
                <span class="text-slate-400">經度</span>
                <span class="text-slate-50 font-mono">{{ activeNode.lon.toFixed(4) }}°E</span>
              </div>
              <div v-if="activeNode.lat && activeNode.lon" class="flex items-center justify-between py-1.5 border-b border-slate-700/50">
                <span class="text-slate-400">緯度</span>
                <span class="text-slate-50 font-mono">{{ activeNode.lat.toFixed(4) }}°N</span>
              </div>
            </div>

            <div class="grid grid-cols-3 gap-2 mt-4 text-xs text-slate-300">
              <div class="bg-slate-900/80 rounded-lg p-2 border border-slate-800">
                <div class="text-[11px] text-slate-400">直接連結</div>
                <div class="text-lg font-semibold text-slate-50">{{ activeConnections.length }}</div>
              </div>
              <div class="bg-slate-900/80 rounded-lg p-2 border border-slate-800">
                <div class="text-[11px] text-slate-400">河川</div>
                <div class="text-lg font-semibold text-slate-50">{{ connectionStats.River || 0 }}</div>
              </div>
              <div class="bg-slate-900/80 rounded-lg p-2 border border-slate-800">
                <div class="text-[11px] text-slate-400">測站</div>
                <div class="text-lg font-semibold text-slate-50">{{ (connectionStats.WaterStation || 0) + (connectionStats.RainStation || 0) }}</div>
              </div>
            </div>
          </div>
          <div v-else class="mt-3 text-sm text-slate-400">
            尚未選擇節點，點擊圖上任一節點即可開始探索。
          </div>
        </section>

        <section class="p-6 border-b border-slate-800">
          <div class="flex items-center justify-between mb-3">
            <div>
              <p class="text-xs uppercase tracking-[0.2em] text-slate-400">Connections</p>
              <h3 class="text-lg font-semibold text-slate-50">關聯路徑</h3>
            </div>
            <div class="text-[11px] text-slate-400">{{ activeConnections.length }} 條</div>
          </div>

          <div v-if="activeConnections.length" class="space-y-2">
            <button
              v-for="conn in activeConnections"
              :key="conn.id + conn.type"
              @click="focusNode(conn.id)"
              class="w-full text-left bg-slate-800/60 hover:bg-slate-800 border border-slate-700 hover:border-sky-400 transition rounded-lg px-3 py-2.5"
            >
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm font-semibold text-slate-50">{{ conn.name }}</p>
                  <p class="text-[11px] text-slate-400">
                    {{ groupMeta[conn.group]?.label || '' }} ・ {{ linkMeta[conn.type]?.label || '連結' }}
                  </p>
                </div>
                <div
                  class="text-xs font-semibold px-2 py-1 rounded-full"
                  :style="{ background: (linkMeta[conn.type]?.color || '#334155') + '22', color: linkMeta[conn.type]?.color || '#cbd5e1', border: '1px solid ' + (linkMeta[conn.type]?.color || '#334155') }"
                >
                  熱度 {{ conn.weight }}
                </div>
              </div>
            </button>
          </div>
          <div v-else class="text-sm text-slate-400">尚無關聯資料，請選擇其他節點。</div>
        </section>

        <section class="p-6">
          <div class="flex items-center justify-between mb-3">
            <div>
              <p class="text-xs uppercase tracking-[0.2em] text-slate-400">Layers</p>
              <h3 class="text-lg font-semibold text-slate-50">分層節點清單</h3>
            </div>
            <span class="text-[11px] text-slate-400">{{ visibleNodes.length }} / {{ allNodes.length }} 節點</span>
          </div>

          <div class="space-y-3">
            <div
              v-for="(meta, groupKey) in groupedNodes"
              :key="groupKey"
              class="border border-slate-800 rounded-xl bg-slate-900/50"
            >
              <div class="flex items-center justify-between px-4 py-2.5 border-b border-slate-800">
                <div class="flex items-center gap-2">
                  <span class="w-2.5 h-2.5 rounded-full" :style="{ background: groupMeta[groupKey].color }"></span>
                  <p class="text-sm font-semibold text-slate-50">{{ groupMeta[groupKey].label }}</p>
                </div>
                <span class="text-[11px] text-slate-400">{{ meta.length }}</span>
              </div>
              <div class="divide-y divide-slate-800">
                <button
                  v-for="node in meta"
                  :key="node.id"
                  @click="focusNode(node.id)"
                  class="w-full text-left px-4 py-2.5 hover:bg-slate-800/70 transition flex items-center justify-between"
                >
                  <span class="text-sm text-slate-100">{{ node.name }}</span>
                  <span
                    class="text-[11px] px-2 py-0.5 rounded-full border"
                    :style="{ borderColor: groupMeta[groupKey].color, color: groupMeta[groupKey].color }"
                  >
                    {{ node.flow || node.region || '查看' }}
                  </span>
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import * as d3 from 'd3';
import neo4jData from '../data/neo4j_graph_data.json';

const container = ref(null);
const svg = ref(null);
const hoveredNode = ref(null);
const tooltip = ref({ x: 0, y: 0 });
const searchTerm = ref('');
const selectedNodeId = ref(null);

// 完整資料（從 Neo4j JSON）
const allNodes = neo4jData.nodes;
const allLinks = neo4jData.links;

// 當前顯示的節點（根據選中狀態過濾）
const visibleNodes = computed(() => {
  // 如果沒有選中任何節點：顯示所有水系
  if (!selectedNodeId.value) {
    return allNodes.filter(n => n.group === 'WaterSystem');
  }

  const visible = new Set();
  const selected = selectedNodeId.value;

  // 情況1: 選中了水系 → 顯示該水系 + 其所有河川（不顯示測站）
  if (selected.startsWith('WS_')) {
    visible.add(selected); // 加入該水系

    allLinks.forEach(link => {
      const sourceId = typeof link.source === 'object' && link.source !== null ? link.source.id : link.source;
      const targetId = typeof link.target === 'object' && link.target !== null ? link.target.id : link.target;

      if (!sourceId || !targetId) return;

      // 找出屬於該水系的河川
      if (targetId === selected && sourceId.startsWith('R_') && link.type === 'BELONGS_TO') {
        visible.add(sourceId); // 加入河川（不加入測站）
      }
    });
  }

  // 情況2: 選中了河川 → 只顯示該河川 + 其所屬水系 + 其支流 + 其測站
  else if (selected.startsWith('R_')) {
    visible.add(selected); // 加入該河川

    allLinks.forEach(link => {
      const sourceId = typeof link.source === 'object' && link.source !== null ? link.source.id : link.source;
      const targetId = typeof link.target === 'object' && link.target !== null ? link.target.id : link.target;

      if (!sourceId || !targetId) return;

      // 找出該河川所屬的水系
      if (sourceId === selected && targetId.startsWith('WS_') && link.type === 'BELONGS_TO') {
        visible.add(targetId); // 加入水系
      }

      // 找出該河川的支流
      if (targetId === selected && sourceId.startsWith('R_') && link.type === 'FLOWS_INTO') {
        visible.add(sourceId); // 加入支流
      }

      // 找出該河川上的測站
      if (targetId === selected && sourceId.startsWith('S_') && link.type === 'LOCATED_ON') {
        visible.add(sourceId); // 加入測站
      }

      // 找出匯流到該河川的集水區
      if (targetId === selected && sourceId.startsWith('W_') && link.type === 'DRAINS_TO') {
        visible.add(sourceId); // 加入集水區
      }
    });
  }

  // 情況3: 選中了測站 → 顯示該測站 + 其所在河川 + 該河川所屬水系
  else if (selected.startsWith('S_')) {
    visible.add(selected); // 加入該測站

    allLinks.forEach(link => {
      const sourceId = typeof link.source === 'object' && link.source !== null ? link.source.id : link.source;
      const targetId = typeof link.target === 'object' && link.target !== null ? link.target.id : link.target;

      if (!sourceId || !targetId) return;

      // 找出該測站所在的河川
      if (sourceId === selected && targetId.startsWith('R_') && link.type === 'LOCATED_ON') {
        visible.add(targetId); // 加入河川

        // 找出該河川所屬的水系
        allLinks.forEach(wsLink => {
          const wsSource = typeof wsLink.source === 'object' && wsLink.source !== null ? wsLink.source.id : wsLink.source;
          const wsTarget = typeof wsLink.target === 'object' && wsLink.target !== null ? wsLink.target.id : wsLink.target;

          if (wsSource && wsTarget && wsSource === targetId && wsTarget.startsWith('WS_') && wsLink.type === 'BELONGS_TO') {
            visible.add(wsTarget); // 加入水系
          }
        });
      }
    });
  }

  // 其他類型節點（集水區、流域等）
  else {
    visible.add(selected);

    // 找出相關的節點
    allLinks.forEach(link => {
      const sourceId = typeof link.source === 'object' && link.source !== null ? link.source.id : link.source;
      const targetId = typeof link.target === 'object' && link.target !== null ? link.target.id : link.target;

      if (!sourceId || !targetId) return;

      if (sourceId === selected) visible.add(targetId);
      if (targetId === selected) visible.add(sourceId);
    });
  }

  return allNodes.filter(n => visible.has(n.id));
});

// 當前顯示的連結（只顯示可見節點之間的連結）
const visibleLinks = computed(() => {
  const visibleIds = new Set(visibleNodes.value.map(n => n.id));
  return allLinks.filter(link => {
    const sourceId = typeof link.source === 'object' && link.source !== null ? link.source.id : link.source;
    const targetId = typeof link.target === 'object' && link.target !== null ? link.target.id : link.target;

    // 跳過無效的連結
    if (!sourceId || !targetId) return false;

    return visibleIds.has(sourceId) && visibleIds.has(targetId);
  });
});

let simulation = null;
let nodeElements = null;
let linkElements = null;
let labelElements = null;
let svgElement = null;
let gElement = null;
let zoomBehavior = null;
let ready = false;

const groupMeta = {
  WaterSystem: { label: '水系', short: 'WS', color: '#38bdf8', caption: '主幹水系' },
  River: { label: '河川', short: 'R', color: '#22d3ee', caption: '支流、主流' },
  Watershed: { label: '集水區', short: 'WSH', color: '#2dd4bf', caption: '匯流斷面' },
  Basin: { label: '流域', short: 'B', color: '#a855f7', caption: '分區管理' },
  WaterStation: { label: '水位站', short: 'WS', color: '#f472b6', caption: '水位監測' },
  RainStation: { label: '雨量站', short: 'RS', color: '#fb923c', caption: '雨量監測' },
  Station: { label: '測站', short: 'ST', color: '#e879f9', caption: '監測節點' },
};

const linkMeta = {
  BELONGS_TO: { label: '主幹歸屬', color: '#60a5fa' },
  FLOWS_INTO: { label: '支流匯入', color: '#22d3ee' },
  TRIBUTARY_TO: { label: '支流匯入', color: '#22d3ee' },
  DRAINS_TO: { label: '集水區匯流', color: '#2dd4bf' },
  PART_OF: { label: '流域分區', color: '#a855f7' },
  LOCATED_ON: { label: '測站監測', color: '#f472b6' },
  GAUGES: { label: '測站監測', color: '#f472b6' },
  DISCHARGES: { label: '沿海出海', color: '#fb923c' },
  FEEDS: { label: '供水支援', color: '#a3e635' },
};

const nodesById = new Map(allNodes.map((n) => [n.id, n]));
const groupedNodes = computed(() => ({
  WaterSystem: visibleNodes.value.filter((n) => n.group === 'WaterSystem'),
  River: visibleNodes.value.filter((n) => n.group === 'River'),
  Watershed: visibleNodes.value.filter((n) => n.group === 'Watershed'),
  Basin: visibleNodes.value.filter((n) => n.group === 'Basin'),
  WaterStation: visibleNodes.value.filter((n) => n.group === 'WaterStation'),
  RainStation: visibleNodes.value.filter((n) => n.group === 'RainStation'),
}));

const activeNode = computed(() => nodesById.get(selectedNodeId.value) || null);

const activeConnections = computed(() => {
  if (!selectedNodeId.value) return [];
  const targetId = selectedNodeId.value;
  const collected = [];
  const processedIds = new Set();

  allLinks.forEach((link) => {
    const source = typeof link.source === 'object' && link.source !== null ? link.source.id : link.source;
    const target = typeof link.target === 'object' && link.target !== null ? link.target.id : link.target;

    // 跳過無效的連結
    if (!source || !target) return;

    if (source === targetId || target === targetId) {
      const neighborId = source === targetId ? target : source;

      if (!processedIds.has(neighborId)) {
        const neighbor = nodesById.get(neighborId);
        if (neighbor) {
          collected.push({
            id: neighborId,
            name: neighbor.name,
            group: neighbor.group,
            type: link.type,
            weight: link.weight || 1,
          });
          processedIds.add(neighborId);
        }
      }
    }
  });

  // 特殊處理：如果選中的是水系，額外加入該水系下所有河川的測站
  if (targetId.startsWith('WS_')) {
    // 先找出所有屬於該水系的河川
    const riverIds = new Set();
    allLinks.forEach((link) => {
      const source = typeof link.source === 'object' && link.source !== null ? link.source.id : link.source;
      const target = typeof link.target === 'object' && link.target !== null ? link.target.id : link.target;

      if (target === targetId && source && source.startsWith('R_') && link.type === 'BELONGS_TO') {
        riverIds.add(source);
      }
    });

    // 再找出這些河川上的所有測站
    allLinks.forEach((link) => {
      const source = typeof link.source === 'object' && link.source !== null ? link.source.id : link.source;
      const target = typeof link.target === 'object' && link.target !== null ? link.target.id : link.target;

      if (riverIds.has(target) && source && source.startsWith('S_') && link.type === 'LOCATED_ON') {
        if (!processedIds.has(source)) {
          const station = nodesById.get(source);
          if (station) {
            collected.push({
              id: source,
              name: station.name,
              group: station.group,
              type: link.type,
              weight: link.weight || 1,
            });
            processedIds.add(source);
          }
        }
      }
    });
  }

  return collected.sort((a, b) => b.weight - a.weight);
});

const connectionStats = computed(() => {
  const stats = {};
  activeConnections.value.forEach((c) => {
    stats[c.group] = (stats[c.group] || 0) + 1;
  });
  return stats;
});

const adjacencyMap = new Map();
allLinks.forEach((link) => {
  const source = typeof link.source === 'object' && link.source !== null ? link.source.id : link.source;
  const target = typeof link.target === 'object' && link.target !== null ? link.target.id : link.target;

  // 跳過無效的連結
  if (!source || !target) return;

  const { weight, type } = link;
  if (!adjacencyMap.has(source)) adjacencyMap.set(source, []);
  if (!adjacencyMap.has(target)) adjacencyMap.set(target, []);
  adjacencyMap.get(source).push({ id: target, weight, type });
  adjacencyMap.get(target).push({ id: source, weight, type });
});

const applySearch = () => {
  if (!searchTerm.value) return;
  const keyword = searchTerm.value.toLowerCase();
  const found = allNodes.find(
    (n) => n.name.toLowerCase().includes(keyword) || (groupMeta[n.group] && groupMeta[n.group].label.toLowerCase().includes(keyword)),
  );
  if (found) {
    focusNode(found.id);
  }
};

const focusNode = (id) => {
  selectedNodeId.value = id;
  if (ready) {
    highlightNode(id);
    // 自動將選中的節點及其相關節點移到畫面中心
    centerOnNode(id);
  }
};

const centerOnNode = (nodeId) => {
  if (!svgElement || !gElement || !zoomBehavior || !simulation) return;

  const nodes = simulation.nodes();
  const targetNode = nodes.find(n => n.id === nodeId);
  if (!targetNode || !targetNode.x || !targetNode.y) return;

  // 找出所有相關的節點（鄰居）
  const neighbors = adjacencyMap.get(nodeId) || [];
  const relatedNodeIds = new Set([nodeId, ...neighbors.map(n => n.id)]);
  const relatedNodes = nodes.filter(n => relatedNodeIds.has(n.id) && n.x && n.y);

  if (relatedNodes.length === 0) return;

  // 計算相關節點的邊界
  const bounds = relatedNodes.reduce(
    (acc, node) => {
      acc.minX = Math.min(acc.minX, node.x);
      acc.maxX = Math.max(acc.maxX, node.x);
      acc.minY = Math.min(acc.minY, node.y);
      acc.maxY = Math.max(acc.maxY, node.y);
      return acc;
    },
    { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity }
  );

  const rect = container.value.getBoundingClientRect();
  const width = rect.width;
  const height = rect.height;

  // 計算需要的縮放比例和平移量
  const dx = bounds.maxX - bounds.minX;
  const dy = bounds.maxY - bounds.minY;
  const x = (bounds.minX + bounds.maxX) / 2;
  const y = (bounds.minY + bounds.maxY) / 2;

  // 添加一些 padding，確保節點不會貼邊
  const padding = 100;
  const scale = Math.min(6, 0.8 / Math.max((dx + padding * 2) / width, (dy + padding * 2) / height));
  const translate = [width / 2 - scale * x, height / 2 - scale * y];

  // 使用平滑過渡移動視圖
  svgElement
    .transition()
    .duration(750)
    .call(zoomBehavior.transform, d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale));
};

const resetView = () => {
  selectedNodeId.value = null;
  if (!nodeElements || !linkElements || !labelElements) return;

  nodeElements
    .attr('opacity', 0.95)
    .attr('stroke', '#0f172a')
    .attr('stroke-width', 1.5);

  linkElements
    .attr('opacity', 0.35)
    .attr('stroke', (l) => linkMeta[l.type]?.color || '#334155')
    .attr('marker-end', (l) => `url(#arrow-${l.type})`)
    .attr('stroke-width', 1.4);

  labelElements.attr('opacity', 0.9);
};

const fitToScreen = () => {
  if (!svgElement || !gElement || !zoomBehavior || !simulation) return;

  const nodes = simulation.nodes();
  if (nodes.length === 0) return;

  // 計算所有節點的邊界
  const bounds = nodes.reduce(
    (acc, node) => {
      if (node.x && node.y) {
        acc.minX = Math.min(acc.minX, node.x);
        acc.maxX = Math.max(acc.maxX, node.x);
        acc.minY = Math.min(acc.minY, node.y);
        acc.maxY = Math.max(acc.maxY, node.y);
      }
      return acc;
    },
    { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity }
  );

  const rect = container.value.getBoundingClientRect();
  const width = rect.width;
  const height = rect.height;

  const dx = bounds.maxX - bounds.minX;
  const dy = bounds.maxY - bounds.minY;
  const x = (bounds.minX + bounds.maxX) / 2;
  const y = (bounds.minY + bounds.maxY) / 2;

  const scale = Math.min(8, 0.9 / Math.max(dx / width, dy / height));
  const translate = [width / 2 - scale * x, height / 2 - scale * y];

  svgElement
    .transition()
    .duration(750)
    .call(zoomBehavior.transform, d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale));
};

const getNodeId = (val) => (typeof val === 'object' ? val.id : val);

const highlightNode = (nodeId) => {
  if (!nodeElements || !linkElements || !labelElements) return;
  if (!nodeId) {
    resetView();
    return;
  }

  const neighbors = adjacencyMap.get(nodeId) || [];
  const focusSet = new Set([nodeId, ...neighbors.map((n) => n.id)]);

  nodeElements
    .attr('opacity', (d) => (focusSet.has(d.id) ? 1 : 0.15))
    .attr('stroke', (d) => {
      if (d.id === nodeId) return '#fbbf24';
      return focusSet.has(d.id) ? '#38bdf8' : '#0f172a';
    })
    .attr('stroke-width', (d) => {
      if (d.id === nodeId) return 4;
      return focusSet.has(d.id) ? 2.2 : 1.4;
    })
    .attr('filter', (d) => (d.id === nodeId ? 'url(#glow-strong)' : focusSet.has(d.id) ? 'url(#glow-soft)' : null));

  linkElements
    .attr('opacity', (l) => {
      const s = getNodeId(l.source);
      const t = getNodeId(l.target);
      return s === nodeId || t === nodeId || (focusSet.has(s) && focusSet.has(t)) ? 0.95 : 0.06;
    })
    .attr('stroke', (l) => {
      const s = getNodeId(l.source);
      const t = getNodeId(l.target);
      const active = s === nodeId || t === nodeId;
      return active ? linkMeta[l.type]?.color || '#38bdf8' : '#1f2937';
    })
    .attr('stroke-width', (l) => {
      const s = getNodeId(l.source);
      const t = getNodeId(l.target);
      return s === nodeId || t === nodeId ? 2.6 : 1.2;
    })
    .attr('marker-end', (l) => {
      const s = getNodeId(l.source);
      const t = getNodeId(l.target);
      const active = s === nodeId || t === nodeId || (focusSet.has(s) && focusSet.has(t));
      return active ? `url(#arrow-${l.type})` : 'url(#arrow-dim)';
    });

  labelElements.attr('opacity', (d) => (focusSet.has(d.id) ? 0.98 : 0.12));
};

onMounted(() => {
  if (!container.value || !svg.value) return;
  const nodes = visibleNodes.value.map((d) => ({ ...d }));
  const links = visibleLinks.value.map((l) => ({ ...l }));

  const rect = container.value.getBoundingClientRect();
  const width = rect.width;
  const height = rect.height;

  const svgEl = d3.select(svg.value);
  svgElement = svgEl; // 儲存引用
  const defs = svgEl.append('defs');

  // arrow markers
  Object.entries(linkMeta).forEach(([key, meta]) => {
    defs
      .append('marker')
      .attr('id', `arrow-${key}`)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 18)
      .attr('refY', 0)
      .attr('markerWidth', 8)
      .attr('markerHeight', 8)
      .attr('orient', 'auto')
      .append('path')
      .attr('fill', meta.color)
      .attr('d', 'M0,-5L10,0L0,5');
  });

  defs
    .append('marker')
    .attr('id', 'arrow-dim')
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', 18)
    .attr('refY', 0)
    .attr('markerWidth', 8)
    .attr('markerHeight', 8)
    .attr('orient', 'auto')
    .append('path')
    .attr('fill', '#1f2937')
    .attr('d', 'M0,-5L10,0L0,5');

  // glow filters
  const glowStrong = defs.append('filter').attr('id', 'glow-strong');
  glowStrong.append('feGaussianBlur').attr('stdDeviation', 4).attr('result', 'coloredBlur');
  const feMergeStrong = glowStrong.append('feMerge');
  feMergeStrong.append('feMergeNode').attr('in', 'coloredBlur');
  feMergeStrong.append('feMergeNode').attr('in', 'SourceGraphic');

  const glowSoft = defs.append('filter').attr('id', 'glow-soft');
  glowSoft.append('feGaussianBlur').attr('stdDeviation', 2).attr('result', 'coloredBlur');
  const feMergeSoft = glowSoft.append('feMerge');
  feMergeSoft.append('feMergeNode').attr('in', 'coloredBlur');
  feMergeSoft.append('feMergeNode').attr('in', 'SourceGraphic');

  svgEl.attr('viewBox', [0, 0, width, height]);
  const g = svgEl.append('g');
  gElement = g; // 儲存引用

  const zoom = d3.zoom().scaleExtent([0.35, 8]).on('zoom', (event) => {
    g.attr('transform', event.transform);
  });
  zoomBehavior = zoom; // 儲存引用
  svgEl.call(zoom);

  // 台灣地理範圍 (經緯度)
  const taiwanBounds = {
    latMin: 21.9, // 南界 (屏東)
    latMax: 25.3, // 北界 (基隆)
    lonMin: 120.0, // 西界 (澎湖)
    lonMax: 122.0, // 東界 (花蓮)
  };

  // 地理座標轉螢幕座標
  const geoToScreen = (lat, lon) => {
    const latRange = taiwanBounds.latMax - taiwanBounds.latMin;
    const lonRange = taiwanBounds.lonMax - taiwanBounds.lonMin;

    // 考慮台灣是南北狹長，給更多垂直空間
    const padding = 80;
    const usableWidth = width - padding * 2;
    const usableHeight = height - padding * 2;

    // 正規化座標 (0-1)
    const normLon = (lon - taiwanBounds.lonMin) / lonRange;
    const normLat = (lat - taiwanBounds.latMin) / latRange;

    // 轉換成螢幕座標 (注意 y 軸反轉：緯度越高在越上方)
    const x = padding + normLon * usableWidth;
    const y = padding + (1 - normLat) * usableHeight;

    return { x, y };
  };

  // 設定節點的初始地理位置
  nodes.forEach((node) => {
    if (node.lat && node.lon) {
      const pos = geoToScreen(node.lat, node.lon);
      node.x = pos.x;
      node.y = pos.y;
      // 水系和測站固定在地理位置，不受力導向影響
      if (node.group === 'WaterSystem' || node.group === 'WaterStation' || node.group === 'RainStation') {
        node.fx = pos.x;
        node.fy = pos.y;
      }
    } else {
      // 沒有座標的節點放中央
      node.x = width / 2;
      node.y = height / 2;
    }
  });

  // 繪製台灣地圖輪廓（簡化但更準確的蕃薯形狀）
  const taiwanOutlineCoords = [
    // 北端（富貴角）順時針繪製
    [121.53, 25.30],
    // 東北角（基隆、瑞芳）
    [121.75, 25.15], [121.92, 25.02],
    // 三貂角
    [122.00, 24.98],
    // 東北海岸（宜蘭）
    [121.92, 24.85], [121.88, 24.70], [121.85, 24.55],
    // 東部海岸（花蓮）- 較平直
    [121.62, 24.20], [121.60, 24.00], [121.55, 23.80],
    [121.52, 23.60], [121.48, 23.40],
    // 台東海岸
    [121.40, 23.20], [121.30, 23.00], [121.15, 22.80],
    [121.00, 22.60], [120.92, 22.45],
    // 南端（鵝鸞鼻）
    [120.86, 21.92],
    // 西南端
    [120.70, 22.00], [120.50, 22.20],
    // 高屏海岸
    [120.35, 22.45], [120.28, 22.65], [120.22, 22.85],
    // 台南、嘉義海岸（內凹的嘉南平原）
    [120.12, 23.05], [120.05, 23.25], [120.02, 23.45],
    [120.05, 23.65], [120.10, 23.85],
    // 彰化、台中海岸
    [120.22, 24.05], [120.35, 24.25], [120.48, 24.40],
    // 新竹、桃園海岸
    [120.65, 24.58], [120.85, 24.75], [121.00, 24.88],
    // 回到北端
    [121.20, 25.05], [121.40, 25.20]
  ];

  const taiwanPathData = taiwanOutlineCoords.map((coord, i) => {
    const pos = geoToScreen(coord[1], coord[0]); // [lon, lat] → geoToScreen(lat, lon)
    return `${i === 0 ? 'M' : 'L'} ${pos.x} ${pos.y}`;
  }).join(' ') + ' Z';

  // 繪製台灣填充（柔和背景）
  g.append('path')
    .attr('d', taiwanPathData)
    .attr('fill', 'rgba(186, 230, 253, 0.08)')
    .attr('stroke', 'none')
    .attr('pointer-events', 'none');

  // 繪製台灣輪廓線
  g.append('path')
    .attr('d', taiwanPathData)
    .attr('fill', 'none')
    .attr('stroke', 'rgba(255, 255, 255, 0.3)')
    .attr('stroke-width', 2)
    .attr('pointer-events', 'none');

  // 使用輕量級的力導向（只用於防止節點重疊，不改變地理位置）
  simulation = d3
    .forceSimulation(nodes)
    .force(
      'link',
      d3
        .forceLink(links)
        .id((d) => d.id)
        .distance(80)
        .strength(0.1), // 降低連結力量，保持地理位置
    )
    .force('charge', d3.forceManyBody().strength(-50))  // 輕微排斥
    .force(
      'collide',
      d3.forceCollide().radius((d) => (d.radius || 12) + 15),
    )
    // 不使用 center force，保持地理位置
    .alphaDecay(0.05) // 快速穩定
    .velocityDecay(0.6); // 降低運動慣性

  linkElements = g
    .append('g')
    .attr('stroke-linecap', 'round')
    .selectAll('line')
    .data(links)
    .join('line')
    .attr('stroke', (l) => linkMeta[l.type]?.color || '#334155')
    .attr('stroke-opacity', 0.35)
    .attr('stroke-width', 1.4)
    .attr('marker-end', (l) => `url(#arrow-${l.type})`);

  nodeElements = g
    .append('g')
    .selectAll('circle')
    .data(nodes)
    .join('circle')
    .attr('r', (d) => d.radius || 12)
    .attr('fill', (d) => groupMeta[d.group]?.color || '#94a3b8')
    .attr('stroke', '#0f172a')
    .attr('stroke-width', 1.5)
    .attr('opacity', 0.95)
    .call(drag(simulation))
    .on('click', (event, d) => {
      event.stopPropagation();
      focusNode(d.id);
    })
    .on('mouseover', (event, d) => {
      hoveredNode.value = d;
      tooltip.value = { x: event.offsetX + 14, y: event.offsetY - 10 };
      d3.select(event.currentTarget).attr('stroke-width', 3);
    })
    .on('mousemove', (event) => {
      tooltip.value = { x: event.offsetX + 14, y: event.offsetY - 10 };
    })
    .on('mouseout', (event, d) => {
      hoveredNode.value = null;
      const strokeWidth = d.id === selectedNodeId.value ? 4 : 1.5;
      d3.select(event.currentTarget).attr('stroke-width', strokeWidth);
    });

  labelElements = g
    .append('g')
    .selectAll('text')
    .data(nodes)
    .join('text')
    .text((d) => d.name)
    .attr('fill', '#e2e8f0')
    .attr('font-size', 11)
    .attr('font-weight', 600)
    .attr('stroke', '#0f172a')
    .attr('stroke-width', 0.2)
    .attr('opacity', 0.9)
    .attr('pointer-events', 'none');

  simulation.on('tick', () => {
    linkElements
      .attr('x1', (d) => d.source.x)
      .attr('y1', (d) => d.source.y)
      .attr('x2', (d) => d.target.x)
      .attr('y2', (d) => d.target.y);

    nodeElements.attr('cx', (d) => d.x).attr('cy', (d) => d.y);

    labelElements
      .attr('x', (d) => d.x + (d.radius || 12) + 6)
      .attr('y', (d) => d.y + 4);
  });

  const resizeObserver = new ResizeObserver((entries) => {
    for (const entry of entries) {
      const { width: w, height: h } = entry.contentRect;
      svgEl.attr('viewBox', [0, 0, w, h]);

      // 重新計算地理位置
      nodes.forEach((node) => {
        if (node.lat && node.lon) {
          const taiwanBounds = {
            latMin: 21.9,
            latMax: 25.3,
            lonMin: 120.0,
            lonMax: 122.0,
          };
          const latRange = taiwanBounds.latMax - taiwanBounds.latMin;
          const lonRange = taiwanBounds.lonMax - taiwanBounds.lonMin;
          const padding = 80;
          const usableWidth = w - padding * 2;
          const usableHeight = h - padding * 2;
          const normLon = (node.lon - taiwanBounds.lonMin) / lonRange;
          const normLat = (node.lat - taiwanBounds.latMin) / latRange;
          node.x = padding + normLon * usableWidth;
          node.y = padding + (1 - normLat) * usableHeight;
        }
      });

      simulation.alpha(0.2).restart();
    }
  });

  resizeObserver.observe(container.value);
  ready = true;
  highlightNode(selectedNodeId.value);

  // 初始化時自動適應視圖
  setTimeout(() => {
    fitToScreen();
  }, 500);

  onUnmounted(() => {
    resizeObserver.disconnect();
    simulation.stop();
  });
});

watch(selectedNodeId, (val) => {
  if (ready) highlightNode(val);
});

// 監控可見節點變化，重新渲染圖譜
watch([visibleNodes, visibleLinks], () => {
  if (!ready || !simulation) return;

  const nodes = visibleNodes.value.map((d) => ({ ...d }));
  const links = visibleLinks.value.map((l) => ({ ...l }));

  // 保留原有節點的位置
  const oldNodesMap = new Map();
  if (simulation.nodes()) {
    simulation.nodes().forEach(n => {
      oldNodesMap.set(n.id, { x: n.x, y: n.y, vx: n.vx, vy: n.vy });
    });
  }

  // 恢復已存在節點的位置
  nodes.forEach(node => {
    const old = oldNodesMap.get(node.id);
    if (old) {
      node.x = old.x;
      node.y = old.y;
      node.vx = old.vx;
      node.vy = old.vy;
    } else if (node.lat && node.lon) {
      // 新節點使用地理位置
      const rect = container.value.getBoundingClientRect();
      const taiwanBounds = {
        latMin: 21.9,
        latMax: 25.3,
        lonMin: 120.0,
        lonMax: 122.0,
      };
      const latRange = taiwanBounds.latMax - taiwanBounds.latMin;
      const lonRange = taiwanBounds.lonMax - taiwanBounds.lonMin;
      const padding = 80;
      const usableWidth = rect.width - padding * 2;
      const usableHeight = rect.height - padding * 2;
      const normLon = (node.lon - taiwanBounds.lonMin) / lonRange;
      const normLat = (node.lat - taiwanBounds.latMin) / latRange;
      node.x = padding + normLon * usableWidth;
      node.y = padding + (1 - normLat) * usableHeight;
      // 水系和測站固定在地理位置
      if (node.group === 'WaterSystem' || node.group === 'WaterStation' || node.group === 'RainStation') {
        node.fx = node.x;
        node.fy = node.y;
      }
    }
  });

  // 更新力導向模擬
  simulation.nodes(nodes);
  simulation.force('link').links(links);

  // 更新 D3 元素
  linkElements = linkElements.data(links, d => `${d.source.id || d.source}-${d.target.id || d.target}-${d.type}`);
  linkElements.exit().remove();
  const linkEnter = linkElements.enter()
    .append('line')
    .attr('stroke', (l) => linkMeta[l.type]?.color || '#334155')
    .attr('stroke-opacity', 0.35)
    .attr('stroke-width', 1.4)
    .attr('marker-end', (l) => `url(#arrow-${l.type})`);
  linkElements = linkEnter.merge(linkElements);

  nodeElements = nodeElements.data(nodes, d => d.id);
  nodeElements.exit().remove();
  const nodeEnter = nodeElements.enter()
    .append('circle')
    .attr('r', (d) => d.radius || 12)
    .attr('fill', (d) => groupMeta[d.group]?.color || '#94a3b8')
    .attr('stroke', '#0f172a')
    .attr('stroke-width', 1.5)
    .attr('opacity', 0.95)
    .call(drag(simulation))
    .on('click', (event, d) => {
      event.stopPropagation();
      focusNode(d.id);
    })
    .on('mouseover', (event, d) => {
      hoveredNode.value = d;
      tooltip.value = { x: event.offsetX + 14, y: event.offsetY - 10 };
      d3.select(event.currentTarget).attr('stroke-width', 3);
    })
    .on('mousemove', (event) => {
      tooltip.value = { x: event.offsetX + 14, y: event.offsetY - 10 };
    })
    .on('mouseout', (event, d) => {
      hoveredNode.value = null;
      const strokeWidth = d.id === selectedNodeId.value ? 4 : 1.5;
      d3.select(event.currentTarget).attr('stroke-width', strokeWidth);
    });
  nodeElements = nodeEnter.merge(nodeElements);

  labelElements = labelElements.data(nodes, d => d.id);
  labelElements.exit().remove();
  const labelEnter = labelElements.enter()
    .append('text')
    .text((d) => d.name)
    .attr('fill', '#e2e8f0')
    .attr('font-size', 11)
    .attr('font-weight', 600)
    .attr('stroke', '#0f172a')
    .attr('stroke-width', 0.2)
    .attr('opacity', 0.9)
    .attr('pointer-events', 'none');
  labelElements = labelEnter.merge(labelElements);

  // 重啟模擬
  simulation.alpha(0.3).restart();
});

function drag(sim) {
  function dragstarted(event) {
    if (!event.active) sim.alphaTarget(0.3).restart();
    event.subject.fx = event.subject.x;
    event.subject.fy = event.subject.y;
  }

  function dragged(event) {
    event.subject.fx = event.x;
    event.subject.fy = event.y;
  }

  function dragended(event) {
    if (!event.active) sim.alphaTarget(0);
    event.subject.fx = null;
    event.subject.fy = null;
  }

  return d3.drag().on('start', dragstarted).on('drag', dragged).on('end', dragended);
}
</script>

<style scoped>
.custom-scroll::-webkit-scrollbar {
  width: 10px;
}

.custom-scroll::-webkit-scrollbar-track {
  background: #0f172a;
}

.custom-scroll::-webkit-scrollbar-thumb {
  background: #1f2937;
  border-radius: 10px;
  border: 2px solid #0f172a;
}

.custom-scroll::-webkit-scrollbar-thumb:hover {
  background: #334155;
}
</style>

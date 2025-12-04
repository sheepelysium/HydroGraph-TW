<template>
  <div class="w-full h-full bg-gray-900 relative overflow-hidden" ref="container">
    <div class="absolute top-4 left-4 z-10 bg-gray-800/80 backdrop-blur p-4 rounded-lg border border-gray-700 shadow-xl">
      <h2 class="text-xl font-bold text-blue-400 mb-2">台灣水文網絡圖</h2>
      <div class="space-y-2 text-sm text-gray-300">
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded-full bg-blue-500"></span> 水系 (WaterSystem)
        </div>
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded-full bg-cyan-500"></span> 河流 (River)
        </div>
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded-full bg-teal-500"></span> 集水區 (Watershed)
        </div>
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded-full bg-violet-500"></span> 流域 (Basin)
        </div>
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded-full bg-fuchsia-500"></span> 測站 (Station)
        </div>
      </div>
    </div>
    
    <svg ref="svg" class="w-full h-full cursor-move"></svg>
    
    <div v-if="hoveredNode" class="absolute pointer-events-none bg-gray-900/90 text-white p-3 rounded border border-blue-500/50 shadow-lg z-20" :style="{ left: tooltipX + 'px', top: tooltipY + 'px' }">
      <div class="font-bold text-lg">{{ hoveredNode.name }}</div>
      <div class="text-xs text-gray-400">{{ groupNameMap[hoveredNode.group] }}</div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, onUnmounted } from 'vue';
import * as d3 from 'd3';
import { mockData } from '../data/mockData';

const container = ref(null);
const svg = ref(null);
const hoveredNode = ref(null);
const tooltipX = ref(0);
const tooltipY = ref(0);

let simulation = null;

const colorMap = {
  WaterSystem: '#3b82f6', // blue-500
  River: '#06b6d4',      // cyan-500 (darker/cooler than 400)
  Watershed: '#14b8a6',  // teal-500 (cooler than green)
  Basin: '#8b5cf6',      // violet-500 (cool purple instead of yellow)
  Station: '#d946ef'     // fuchsia-500 (cool pink instead of red)
};

const groupNameMap = {
  WaterSystem: '水系',
  River: '河流',
  Watershed: '集水區',
  Basin: '流域',
  Station: '測站'
};

onMounted(() => {
  if (!container.value || !svg.value) return;

  // Deep clone data to avoid mutation issues during HMR or re-renders
  const nodes = JSON.parse(JSON.stringify(mockData.nodes));
  const links = JSON.parse(JSON.stringify(mockData.links));

  // Initial setup
  const svgEl = d3.select(svg.value);
  const g = svgEl.append("g");

  // Get initial dimensions
  const rect = container.value.getBoundingClientRect();
  const width = rect.width;
  const height = rect.height;

  // Set initial viewBox
  svgEl.attr("viewBox", [0, 0, width, height]);

  const zoom = d3.zoom()
    .scaleExtent([0.1, 4])
    .on("zoom", (event) => {
      g.attr("transform", event.transform);
    });

  svgEl.call(zoom);

  // Simulation setup with proper initial center
  simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(d => d.id).distance(150))
    .force("charge", d3.forceManyBody().strength(-800))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collide", d3.forceCollide().radius(d => d.radius + 30));

  // Elements
  const link = g.append("g")
    .attr("stroke", "#4b5563")
    .attr("stroke-opacity", 0.6)
    .selectAll("line")
    .data(links)
    .join("line")
    .attr("stroke-width", 1.5)
    .attr("marker-end", "url(#arrow)");

  // Arrow marker
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

  const node = g.append("g")
    .attr("stroke", "#fff")
    .attr("stroke-width", 1.5)
    .selectAll("circle")
    .data(nodes)
    .join("circle")
    .attr("r", d => d.radius)
    .attr("fill", d => colorMap[d.group] || '#9ca3af')
    .call(drag(simulation));

  const labels = g.append("g")
    .attr("class", "labels")
    .selectAll("text")
    .data(nodes)
    .join("text")
    .attr("dx", 12)
    .attr("dy", ".35em")
    .text(d => d.name)
    .attr("fill", "#e5e7eb")
    .style("font-size", "10px")
    .style("pointer-events", "none")
    .style("opacity", 0.8);

  // Hover interactions
  node.on("mouseover", (event, d) => {
    hoveredNode.value = d;
    tooltipX.value = event.pageX + 10;
    tooltipY.value = event.pageY + 10;
    d3.select(event.currentTarget).attr("stroke", "#60a5fa").attr("stroke-width", 3);
  })
  .on("mousemove", (event) => {
    tooltipX.value = event.pageX + 10;
    tooltipY.value = event.pageY + 10;
  })
  .on("mouseout", (event) => {
    hoveredNode.value = null;
    d3.select(event.currentTarget).attr("stroke", "#fff").attr("stroke-width", 1.5);
  });

  simulation.on("tick", () => {
    link
      .attr("x1", d => d.source.x)
      .attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x)
      .attr("y2", d => d.target.y);

    node
      .attr("cx", d => d.x)
      .attr("cy", d => d.y);

    labels
      .attr("x", d => d.x)
      .attr("y", d => d.y);
  });

  // Resize Observer to handle window resizing and initial size
  const resizeObserver = new ResizeObserver(entries => {
    for (const entry of entries) {
      const { width, height } = entry.contentRect;
      
      // Update SVG viewBox
      svgEl.attr("viewBox", [0, 0, width, height]);
      
      // Update simulation center
      simulation.force("center", d3.forceCenter(width / 2, height / 2));
      simulation.alpha(0.3).restart(); // Re-heat simulation to adjust to new center
    }
  });

  resizeObserver.observe(container.value);

  // Cleanup
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
/* Add any component-specific styles here */
</style>

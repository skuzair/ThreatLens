import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'

const SOURCE_COLORS = {
  camera: '#ef4444',
  logs: '#3b82f6',
  network: '#22c55e',
  rf: '#a855f7',
  file: '#f97316'
}

const SOURCE_ICONS = {
  camera: '📹',
  logs: '💻',
  network: '🌐',
  rf: '📡',
  file: '📁'
}

export default function AttackGraph({ graphData }) {
  const svgRef = useRef()
  const [dimensions, setDimensions] = useState({ width: 800, height: 500 })

  useEffect(() => {
    if (!graphData || !graphData.nodes || !svgRef.current) return

    const width = dimensions.width
    const height = dimensions.height

    // Clear previous graph
    d3.select(svgRef.current).selectAll("*").remove()

    const svg = d3.select(svgRef.current)
      .attr("width", width)
      .attr("height", height)
      .style("background", "#0a0e1a")
      .style("border-radius", "8px")

    // Create arrow marker for edges
    svg.append("defs").append("marker")
      .attr("id", "arrowhead")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 30)
      .attr("refY", 0)
      .attr("markerWidth", 8)
      .attr("markerHeight", 8)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-5L10,0L0,5")
      .attr("fill", "#64748b")

    // Create force simulation
    const simulation = d3.forceSimulation(graphData.nodes)
      .force("link", d3.forceLink(graphData.edges)
        .id(d => d.id)
        .distance(150))
      .force("charge", d3.forceManyBody().strength(-400))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(50))

    // Draw edges with varying thickness based on confidence
    const edges = svg.append("g")
      .selectAll("line")
      .data(graphData.edges)
      .enter()
      .append("line")
      .attr("stroke", "#475569")
      .attr("stroke-width", d => (d.confidence || 0.5) * 4)
      .attr("stroke-opacity", 0.8)
      .attr("marker-end", "url(#arrowhead)")

    // Draw node groups
    const nodeGroups = svg.append("g")
      .selectAll("g")
      .data(graphData.nodes)
      .enter()
      .append("g")
      .style("cursor", "pointer")
      .call(d3.drag()
        .on("start", (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart()
          d.fx = d.x
          d.fy = d.y
        })
        .on("drag", (event, d) => {
          d.fx = event.x
          d.fy = event.y
        })
        .on("end", (event, d) => {
          if (!event.active) simulation.alphaTarget(0)
          d.fx = null
          d.fy = null
        })
      )

    // Draw circles for nodes
    nodeGroups.append("circle")
      .attr("r", d => 20 + (d.score / 10))
      .attr("fill", d => SOURCE_COLORS[d.source_type] || '#64748b')
      .attr("stroke", "#fff")
      .attr("stroke-width", 2)
      .attr("opacity", 0.9)
      .on("mouseover", function() {
        d3.select(this)
          .transition()
          .duration(200)
          .attr("r", d => 25 + (d.score / 10))
          .attr("stroke-width", 3)
      })
      .on("mouseout", function() {
        d3.select(this)
          .transition()
          .duration(200)
          .attr("r", d => 20 + (d.score / 10))
          .attr("stroke-width", 2)
      })

    // Add source icon inside circle
    nodeGroups.append("text")
      .text(d => SOURCE_ICONS[d.source_type] || '?')
      .attr("text-anchor", "middle")
      .attr("dy", "-5px")
      .attr("font-size", "16px")
      .attr("pointer-events", "none")

    // Add score label inside circle
    nodeGroups.append("text")
      .text(d => d.score)
      .attr("text-anchor", "middle")
      .attr("dy", "12px")
      .attr("fill", "white")
      .attr("font-size", "11px")
      .attr("font-weight", "bold")
      .attr("pointer-events", "none")

    // Add label below circle
    nodeGroups.append("text")
      .text(d => d.label || d.id)
      .attr("text-anchor", "middle")
      .attr("dy", "40px")
      .attr("fill", "#94a3b8")
      .attr("font-size", "10px")
      .attr("pointer-events", "none")

    // Add timestamp below label
    nodeGroups.append("text")
      .text(d => d.timestamp ? new Date(d.timestamp).toLocaleTimeString() : '')
      .attr("text-anchor", "middle")
      .attr("dy", "52px")
      .attr("fill", "#64748b")
      .attr("font-size", "8px")
      .attr("pointer-events", "none")

    // Update positions on each tick
    simulation.on("tick", () => {
      edges
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y)

      nodeGroups.attr("transform", d => `translate(${d.x},${d.y})`)
    })

    return () => {
      simulation.stop()
    }
  }, [graphData, dimensions])

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '16px'
      }}>
        <h3 style={{ color: '#e2e8f0', margin: 0 }}>
          Causal Attack Graph
        </h3>
        <div style={{ display: 'flex', gap: '12px', fontSize: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <div style={{ width: '12px', height: '12px', background: SOURCE_COLORS.camera, borderRadius: '50%' }}></div>
            <span style={{ color: '#94a3b8' }}>Camera</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <div style={{ width: '12px', height: '12px', background: SOURCE_COLORS.logs, borderRadius: '50%' }}></div>
            <span style={{ color: '#94a3b8' }}>Logs</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <div style={{ width: '12px', height: '12px', background: SOURCE_COLORS.network, borderRadius: '50%' }}></div>
            <span style={{ color: '#94a3b8' }}>Network</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <div style={{ width: '12px', height: '12px', background: SOURCE_COLORS.rf, borderRadius: '50%' }}></div>
            <span style={{ color: '#94a3b8' }}>RF</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <div style={{ width: '12px', height: '12px', background: SOURCE_COLORS.file, borderRadius: '50%' }}></div>
            <span style={{ color: '#94a3b8' }}>File</span>
          </div>
        </div>
      </div>
      
      <div style={{ 
        background: '#0a0e1a', 
        borderRadius: '8px', 
        border: '1px solid #1e2d45',
        overflow: 'hidden'
      }}>
        <svg ref={svgRef} style={{ display: 'block', width: '100%' }} />
      </div>

      <div style={{ 
        marginTop: '12px', 
        fontSize: '11px', 
        color: '#64748b',
        textAlign: 'center'
      }}>
        💡 Drag nodes to rearrange • Edge thickness = causal confidence • Node size = risk score
      </div>
    </div>
  )
}

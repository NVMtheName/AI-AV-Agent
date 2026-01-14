import React, { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'

const NetworkTopology = ({ devices, onDeviceClick }) => {
  const svgRef = useRef()
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 })

  useEffect(() => {
    const updateDimensions = () => {
      if (svgRef.current) {
        const { width, height } = svgRef.current.getBoundingClientRect()
        setDimensions({ width, height })
      }
    }

    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  useEffect(() => {
    if (!dimensions.width || !dimensions.height || !devices.length) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const { width, height } = dimensions

    // Create nodes from devices
    const nodes = devices.map((device, i) => ({
      id: device.id || i,
      name: device.device_name || device.name || `Device ${i}`,
      status: device.status || 'unknown',
      type: device.device_type || device.type || 'unknown',
      x: Math.random() * width,
      y: Math.random() * height,
      ...device,
    }))

    // Create links (simple mesh for demonstration)
    const links = []
    nodes.forEach((node, i) => {
      if (i > 0) {
        links.push({
          source: nodes[0],
          target: node,
          status: node.status,
        })
      }
    })

    // Create force simulation
    const simulation = d3
      .forceSimulation(nodes)
      .force('link', d3.forceLink(links).distance(150))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40))

    // Create links
    const link = svg
      .append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('class', 'network-link')
      .attr('stroke-width', 2)
      .attr('stroke', (d) => {
        switch (d.status?.toLowerCase()) {
          case 'available':
          case 'online':
            return '#10b981'
          case 'warning':
            return '#f59e0b'
          case 'offline':
          case 'critical':
            return '#ef4444'
          default:
            return '#4b5563'
        }
      })

    // Create node groups
    const node = svg
      .append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('class', 'network-node')
      .call(
        d3
          .drag()
          .on('start', dragstarted)
          .on('drag', dragged)
          .on('end', dragended)
      )
      .on('click', (event, d) => {
        onDeviceClick(d)
      })

    // Add circles to nodes
    node
      .append('circle')
      .attr('r', 25)
      .attr('fill', (d) => {
        switch (d.status?.toLowerCase()) {
          case 'available':
          case 'online':
            return '#10b981'
          case 'warning':
            return '#f59e0b'
          case 'offline':
          case 'critical':
            return '#ef4444'
          default:
            return '#6b7280'
        }
      })
      .attr('stroke', '#1f2937')
      .attr('stroke-width', 3)

    // Add status indicator (pulse)
    node
      .filter((d) => d.status?.toLowerCase() === 'available' || d.status?.toLowerCase() === 'online')
      .append('circle')
      .attr('r', 25)
      .attr('fill', 'none')
      .attr('stroke', '#10b981')
      .attr('stroke-width', 2)
      .attr('opacity', 0)
      .transition()
      .duration(2000)
      .ease(d3.easeLinear)
      .attr('r', 35)
      .attr('opacity', 0)
      .on('end', function repeat() {
        d3.select(this)
          .attr('r', 25)
          .attr('opacity', 0.8)
          .transition()
          .duration(2000)
          .ease(d3.easeLinear)
          .attr('r', 35)
          .attr('opacity', 0)
          .on('end', repeat)
      })

    // Add labels
    node
      .append('text')
      .text((d) => d.name.substring(0, 10))
      .attr('text-anchor', 'middle')
      .attr('dy', 50)
      .attr('fill', '#9ca3af')
      .attr('font-size', '12px')
      .attr('font-weight', '500')

    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d) => d.source.x)
        .attr('y1', (d) => d.source.y)
        .attr('x2', (d) => d.target.x)
        .attr('y2', (d) => d.target.y)

      node.attr('transform', (d) => `translate(${d.x},${d.y})`)
    })

    // Drag functions
    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart()
      d.fx = d.x
      d.fy = d.y
    }

    function dragged(event, d) {
      d.fx = event.x
      d.fy = event.y
    }

    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0)
      d.fx = null
      d.fy = null
    }

    return () => {
      simulation.stop()
    }
  }, [dimensions, devices, onDeviceClick])

  return (
    <div className="card h-full">
      <div className="p-4 border-b border-dark-800">
        <h3 className="text-lg font-semibold text-white">Network Topology</h3>
        <p className="text-sm text-gray-500">Interactive device map</p>
      </div>
      <div className="relative h-[600px]">
        <svg ref={svgRef} className="w-full h-full" />
        {devices.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center text-gray-500">
            No devices to display
          </div>
        )}
      </div>
    </div>
  )
}

export default NetworkTopology

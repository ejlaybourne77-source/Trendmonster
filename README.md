// VISUAL INDICATORS
// ============================================================================

plot(showSMA ? smaForPlot : na, "50-Week SMA", color=marketOnWeekly ? colorUptrend : colorDowntrend, linewidth=2)
bgcolor(bgColor, title="Strategy State")

// ============================================================================
// COMBINED TABLE - ALL INFO IN ONE PLACE
// ============================================================================

var table mainTable = table.new(position.top_right, 2, 28, bgcolor=colorTableBg, border_width=2, border_color=colorHeaderBg)

if barstate.islast
    row = 0
    
    // HEADER
    if showCurrentState
        table.cell(mainTable, 0, row, "TRENDMONSTER STRATEGY", text_color=colorTextWhite, bgcolor=colorHeaderBg, text_size=size.large, text_halign=text.align_center)
        table.merge_cells(mainTable, 0, row, 1, row)
        row := row + 1
        
        // Signal basis note
        table.cell(mainTable, 0, row, "📊 VIX: Daily Close | Trend/RSI: Weekly Close", text_color=colorTextYellow, bgcolor=color.new(colorHeaderBg, 70), text_size=size.small, text_halign=text.align_center)
        table.merge_cells(mainTable, 0, row, 1, row)
        row := row + 1
        
        // CURRENT STATE
        table.cell(mainTable, 0, row, "CURRENT STATE", text_color=colorTextWhite, bgcolor=color.new(colorHeaderBg, 50), text_size=size.normal, text_halign=text.align_center)
        table.merge_cells(mainTable, 0, row, 1, row)
        row := row + 1
        
        table.cell(mainTable, 0, row, "Posture:", text_color=colorTextWhite, bgcolor=colorRowBg1, text_size=size.normal)
        table.cell(mainTable, 1, row, posture, text_color=colorTextWhite, bgcolor=postureColor, text_size=size.normal, text_halign=text.align_center)
        row := row + 1
        
        table.cell(mainTable, 0, row, "Trend (Weekly):", text_color=colorTextWhite, bgcolor=colorRowBg2, text_size=size.normal)
        table.cell(mainTable, 1, row, marketOnWeekly ? "✓ UPTREND" : "✗ DOWNTREND", text_color=colorTextWhite, bgcolor=marketOnWeekly ? colorUptrend : colorDowntrend, text_size=size.normal, text_halign=text.align_center)
        row := row + 1
    
    // PORTFOLIO MIX
    if showPortfolioMix
        table.cell(mainTable, 0, row, "PORTFOLIO MIX", text_color=colorTextWhite, bgcolor=color.new(colorHeaderBg, 50), text_size=size.normal, text_halign=text.align_center)
        table.merge_cells(mainTable, 0, row, 1, row)
        row := row + 1
        
        table.cell(mainTable, 0, row, "SPY:", text_color=colorTextWhite, bgcolor=colorRowBg1, text_size=size.normal)
        table.cell(mainTable, 1, row, str.tostring(spyAllocation * 100, "#.0") + "%", text_color=colorTextWhite, bgcolor=colorSPY, text_size=size.normal, text_halign=text.align_center)
        row := row + 1
        
        table.cell(mainTable, 0, row, "TQQQ:", text_color=colorTextWhite, bgcolor=colorRowBg2, text_size=size.normal)
        table.cell(mainTable, 1, row, str.tostring(tqqqAllocation * 100, "#.0") + "%", text_color=colorTextWhite, bgcolor=colorTQQQ, text_size=size.normal, text_halign=text.align_center)
        row := row + 1
        
        table.cell(mainTable, 0, row, "Cash:", text_color=colorTextWhite, bgcolor=colorRowBg1, text_size=size.normal)
        table.cell(mainTable, 1, row, str.tostring(cashAllocation * 100, "#.0") + "%", text_color=colorTextWhite, bgcolor=colorCash, text_size=size.normal, text_halign=text.align_center)
        row := row + 1
    
    // INDICATORS
    if showIndicators
        table.cell(mainTable, 0, row, "INDICATORS", text_color=colorTextWhite, bgcolor=color.new(colorHeaderBg, 50), text_size=size.normal, text_halign=text.align_center)
        table.merge_cells(mainTable, 0, row, 1, row)
        row := row + 1
        
        // VIX ratio - confirmed daily close
        table.cell(mainTable, 0, row, "VIX Ratio (Daily):", text_color=colorTextWhite, bgcolor=colorRowBg1, text_size=size.normal)
        table.cell(mainTable, 1, row, str.tostring(vixRatioDaily, "#.###") + " △ " + vixLevel, text_color=colorTextWhite, bgcolor=vixColor, text_size=size.normal, text_halign=text.align_center)
        row := row + 1
        
        // Live VIX for reference only
        table.cell(mainTable, 0, row, "VIX Ratio (Live):", text_color=color.new(colorTextWhite, 50), bgcolor=colorRowBg2, text_size=size.small)
        table.cell(mainTable, 1, row, str.tostring(vixRatioCurrent, "#.###"), text_color=color.new(colorTextWhite, 50), bgcolor=colorRowBg2, text_size=size.small, text_halign=text.align_center)
        row := row + 1
        
        // RSI - confirmed weekly close
        table.cell(mainTable, 0, row, "RSI (14W Weekly):", text_color=colorTextWhite, bgcolor=colorRowBg1, text_size=size.normal)
        table.cell(mainTable, 1, row, str.tostring(weeklyRSI, "#.0"), text_color=colorTextWhite, bgcolor=colorRowBg1, text_size=size.normal, text_halign=text.align_center)
        row := row + 1
        
        // Weekly close vs SMA
        table.cell(mainTable, 0, row, "Weekly Close:", text_color=colorTextWhite, bgcolor=colorRowBg2, text_size=size.normal)
        table.cell(mainTable, 1, row, str.tostring(weeklyClose, "#.##"), text_color=colorTextWhite, bgcolor=colorRowBg2, text_size=size.normal, text_halign=text.align_center)
        row := row + 1
        
        table.cell(mainTable, 0, row, "50W SMA:", text_color=colorTextWhite, bgcolor=colorRowBg1, text_size=size.normal)
        table.cell(mainTable, 1, row, str.tostring(weeklySMA, "#.##"), text_color=colorTextWhite, bgcolor=colorRowBg1, text_size=size.normal, text_halign=text.align_center)
        row := row + 1
    
    // VIX ALLOCATION RANGES
    if showVIXRanges
        table.cell(mainTable, 0, row, "VIX ALLOCATION RANGES", text_color=colorTextWhite, bgcolor=color.new(colorHeaderBg, 50), text_size=size.small, text_halign=text.align_center)
        table.merge_cells(mainTable, 0, row, 1, row)
        row := row + 1
        
        r1 = vixRatioDaily < 0.80 ? colorVeryLow : colorRowBg1
        table.cell(mainTable, 0, row, "< 0.80 → 30/70", text_color=colorTextWhite, bgcolor=r1, text_size=size.small, text_halign=text.align_center)
        table.merge_cells(mainTable, 0, row, 1, row)
        row := row + 1
        
        r2 = vixRatioDaily >= 0.80 and vixRatioDaily < 0.90 ? colorLow : colorRowBg1
        table.cell(mainTable, 0, row, "0.80-0.90 → 50/50", text_color=colorTextWhite, bgcolor=r2, text_size=size.small, text_halign=text.align_center)
        table.merge_cells(mainTable, 0, row, 1, row)
        row := row + 1
        
        r3 = vixRatioDaily >= 0.90 and vixRatioDaily < 0.95 ? colorModerate : colorRowBg1
        table.cell(mainTable, 0, row, "0.90-0.95 → 60/40", text_color=colorTextWhite, bgcolor=r3, text_size=size.small, text_halign=text.align_center)
        table.merge_cells(mainTable, 0, row, 1, row)
        row := row + 1
        
        r4 = vixRatioDaily >= 0.95 and vixRatioDaily < 1.05 ? colorElevated : colorRowBg1
        table.cell(mainTable, 0, row, "0.95-1.05 → 75/25", text_color=colorTextWhite, bgcolor=r4, text_size=size.small, text_halign=text.align_center)
        table.merge_cells(mainTable, 0, row, 1, row)
        row := row + 1
        
        r5 = vixRatioDaily >= 1.05 ? colorHigh : colorRowBg1
        table.cell(mainTable, 0, row, "> 1.05 → 85/15", text_color=colorTextWhite, bgcolor=r5, text_size=size.small, text_halign=text.align_center)
        table.merge_cells(mainTable, 0, row, 1, row)
        row := row + 1
    
    // REBALANCING INSTRUCTIONS
    if showRebalancing
        table.cell(mainTable, 0, row, "REBALANCING INSTRUCTIONS", text_color=colorTextYellow, bgcolor=color.new(colorHeaderBg, 30), text_size=size.normal, text_halign=text.align_center)
        table.merge_cells(mainTable, 0, row, 1, row)
        row := row + 1
        
        if rebalanceNeeded
            table.cell(mainTable, 0, row, "⚠️ REBALANCE REQUIRED", text_color=colorTextWhite, bgcolor=colorTextOrange, text_size=size.normal, text_halign=text.align_center)
            table.merge_cells(mainTable, 0, row, 1, row)
            row := row + 1
            
            table.cell(mainTable, 0, row, "Execute: Next trading day at open", text_color=colorTextYellow, bgcolor=colorRowBg1, text_size=size.small, text_halign=text.align_center)
            table.merge_cells(mainTable, 0, row, 1, row)
            row := row + 1
            
            spyAction = spyChange > 0 ? "BUY" : spyChange < 0 ? "SELL" : "HOLD"
            spyText = spyAction == "HOLD" ? "SPY: No change" : spyAction + " " + str.tostring(math.abs(spyChange) * 100, "#.0") + "% SPY"
            spyBg = spyAction == "BUY" ? colorUptrend : spyAction == "SELL" ? colorDowntrend : colorRowBg1
            table.cell(mainTable, 0, row, spyText, text_color=colorTextWhite, bgcolor=spyBg, text_size=size.normal, text_halign=text.align_center)
            table.merge_cells(mainTable, 0, row, 1, row)
            row := row + 1
            
            tqqqAction = tqqqChange > 0 ? "BUY" : tqqqChange < 0 ? "SELL" : "HOLD"
            tqqqText = tqqqAction == "HOLD" ? "TQQQ: No change" : tqqqAction + " " + str.tostring(math.abs(tqqqChange) * 100, "#.0") + "% TQQQ"
            tqqqBg = tqqqAction == "BUY" ? colorUptrend : tqqqAction == "SELL" ? colorDowntrend : colorRowBg1
            table.cell(mainTable, 0, row, tqqqText, text_color=colorTextWhite, bgcolor=tqqqBg, text_size=size.normal, text_halign=text.align_center)
            table.merge_cells(mainTable, 0, row, 1, row)
        else
            table.cell(mainTable, 0, row, "✓ NO REBALANCE NEEDED", text_color=colorTextWhite, bgcolor=colorUptrend, text_size=size.normal, text_halign=text.align_center)
            table.merge_cells(mainTable, 0, row, 1, row)
            row := row + 1
            
            table.cell(mainTable, 0, row, "Current allocation is optimal", text_color=colorTextWhite, bgcolor=colorRowBg1, text_size=size.small, text_halign=text.align_center)
            table.merge_cells(mainTable, 0, row, 1, row)
            row := row + 1
            
            table.cell(mainTable, 0, row, "No action required", text_color=colorTextWhite, bgcolor=colorRowBg1, text_size=size.small, text_halign=text.align_center)
            table.merge_cells(mainTable, 0, row, 1, row)

// ============================================================================
// ALERTS - ONLY FIRE ON CONFIRMED CLOSE DATA CHANGES
// ============================================================================

allocationChanged = confirmedDataChanged and (math.abs(spyChange) > 0.001 or math.abs(tqqqChange) > 0.001)
trendChanged = weeklyDataChanged and ta.change(marketOnWeekly ? 1 : 0) != 0

if enableAlerts and alertOnAllocationChange and allocationChanged
    alert("TrendMonster REBALANCE: SPY " + str.tostring(spyAllocation * 100, "#.0") + "% TQQQ " + str.tostring(tqqqAllocation * 100, "#.0") + "%", alert.freq_once_per_bar)

if enableAlerts and alertOnTrendChange and trendChanged
    alert("TrendMonster TREND: " + (marketOnWeekly ? "UPTREND" : "DOWNTREND"), alert.freq_once_per_bar)

// ============================================================================
// MARKERS - ONLY ON CONFIRMED CLOSE TRIGGERED CHANGES
// ============================================================================

plotshape(rebalanceNeeded and confirmedDataChanged, "Rebalance Alert", shape.circle, location.belowbar, colorTextYellow, size=size.tiny)

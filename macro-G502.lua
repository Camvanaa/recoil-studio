--FPS压枪宏 v2.0  Camvanaa @2026
--支持多枪械配置、按子弹弹道配置、射速计算、垂直/水平倍率

--====================================================================================
-- 基础配置
--====================================================================================
local scriptName = "MountCloud_SCRIPT"
local showLog = true                    -- 是否打印日志
local clickBtn = 1                      -- 触发按键 (左键=1)

-- 按键配置
local toggleBtn = 6                     -- 压枪开关 (G6键) - 按一次开启，再按一次关闭
local gunSwitchUpBtn = 8                -- 切换下一把枪 (DPI+)
local gunSwitchDnBtn = 7                -- 切换上一把枪 (DPI-)
local resetPointBtn = 5                 -- 鼠标复位开关 (前进键)
local resetConfigBtn = 9                -- 配置复位 (G9键)

--====================================================================================
-- 枪械配置
-- rpm: 每分钟射速
-- verticalMul: 垂直倍率 (值越大压枪越强)
-- horizontalMul: 水平倍率 (值越大左右补偿越强)
-- pattern: 弹道配置，每个元素对应一发子弹 {y=垂直后坐力, x=水平后坐力}
--          x正值=向右, x负值=向左
--          y正值=向下(需要向下补偿), 一般都是正值
--====================================================================================
local guns = {
        -- M14
    {
        name = "TestGun",
        rpm = 727,
        verticalMul = 1.0,
        horizontalMul = 1.0,
        pattern = {
            {y=13, x=0},    -- 第2发补偿
            {y=26, x=-7},    -- 第3发补偿
            {y=24, x=-5},    -- 第4发补偿
            {y=24, x=7},    -- 第5发补偿
            {y=20, x=7},    -- 第6发补偿
            {y=19, x=8},    -- 第7发补偿
            {y=18, x=-5},    -- 第8发补偿
            {y=15, x=-4},    -- 第9发补偿
            {y=15, x=3},    -- 第10发补偿
            {y=13, x=7},    -- 第11发补偿
            {y=13, x=-5},    -- 第12发补偿
            {y=11, x=-6},    -- 第13发补偿
            {y=9, x=-5},    -- 第14发补偿
            {y=8, x=-8},    -- 第15发补偿
            {y=8, x=4},    -- 第16发补偿
            {y=12, x=-5},    -- 第17发补偿
            {y=11, x=-6},    -- 第18发补偿
            {y=8, x=-5},    -- 第19发补偿
            {y=10, x=-5},    -- 第20发补偿
            {y=26, x=-9},    -- 第21发补偿
            {y=6, x=-5},    -- 第22发补偿
            {y=7, x=-4},    -- 第23发补偿
            {y=6, x=-4},    -- 第24发补偿
            {y=6, x=-4},    -- 第25发补偿
            {y=6, x=-4},    -- 第26发补偿
            {y=7, x=-4},    -- 第27发补偿
            {y=6, x=-4},    -- 第28发补偿
            {y=7, x=-4},    -- 第29发补偿
            {y=6, x=-4},    -- 第30发补偿
            {y=6, x=-4},    -- 第31发补偿
        }
    },
}

--====================================================================================
-- 运行时状态 (不要修改)
--====================================================================================
local currentGunIndex = 1               -- 当前选择的枪械索引
local currentBullet = 0                 -- 当前子弹计数
local recoilEnabled = false             -- 压枪开关状态
local resetPointState = false           -- 鼠标复位开关
local totalMoveY = 0                    -- 记录总垂直移动量(用于复位)
local totalMoveX = 0                    -- 记录总水平移动量(用于复位)
local errorY = 0                        -- Y轴小数误差累加
local errorX = 0                        -- X轴小数误差累加

--====================================================================================
-- 辅助函数
--====================================================================================

-- 根据RPM计算每发子弹的间隔时间(毫秒)
function getSleepTime()
    local gun = guns[currentGunIndex]
    return math.max(1, math.floor((60000 / gun.rpm) + 0.5))
end

-- 获取当前枪械
function getCurrentGun()
    return guns[currentGunIndex]
end

-- 获取指定补偿段的后坐力数据（返回小数值，不做取整）
function getBulletRecoil(stepIndex)
    local gun = getCurrentGun()
    local pattern = gun.pattern
    
    if #pattern == 0 then
        return 0, 0
    end

    -- 如果补偿段超过配置范围，使用最后一个
    if stepIndex > #pattern then
        stepIndex = #pattern
    end
    if stepIndex < 1 then
        stepIndex = 1
    end
    
    local recoil = pattern[stepIndex]
    local moveY = recoil.y * gun.verticalMul
    local moveX = recoil.x * gun.horizontalMul
    
    return moveY, moveX
end

-- 将小数转换为整数移动量，累加误差到下一次
-- 原理：每次移动取整后，把小数部分累加起来，当累加值>=1时补偿
function applyMovement(rawY, rawX)
    -- 加上之前累积的误差
    local totalY = rawY + errorY
    local totalX = rawX + errorX
    
    -- 取整作为实际移动量
    local moveY = math.floor(totalY)
    local moveX = math.floor(totalX)
    
    -- 保存小数误差到下一次
    errorY = totalY - moveY
    errorX = totalX - moveX
    
    return moveY, moveX
end

-- 切换枪械
function switchGun(delta)
    currentGunIndex = currentGunIndex + delta
    if currentGunIndex < 1 then
        currentGunIndex = #guns
    end
    if currentGunIndex > #guns then
        currentGunIndex = 1
    end
    local gun = getCurrentGun()
    log("Switch to gun: %s (RPM=%d, vMul=%.1f, hMul=%.1f)", 
        gun.name, gun.rpm, gun.verticalMul, gun.horizontalMul)
end

-- 日志函数
function log(str, ...)
    if showLog then
        OutputLogMessage(scriptName .. "-[INFO]-" .. str .. "\n", ...)
    end
end

function sleepWhileHolding(duration)
    local elapsed = 0
    while elapsed < duration do
        if not IsMouseButtonPressed(clickBtn) then
            return false
        end

        local slice = math.min(4, duration - elapsed)
        Sleep(slice)
        elapsed = elapsed + slice
    end

    return true
end

--====================================================================================
-- 核心功能
--====================================================================================

-- 开启左键事件报告
EnablePrimaryMouseButtonEvents(true)

-- 主事件处理
function OnEvent(event, arg)
    log("event=%s,arg=%s", event, arg)
    
    -- 压枪开关 (G6键)
    if event == "MOUSE_BUTTON_PRESSED" and arg == toggleBtn then
        recoilEnabled = not recoilEnabled
        log("Recoil control: %s", recoilEnabled and "ON" or "OFF")
        return
    end
    
    -- 切换枪械 - 下一把
    if event == "MOUSE_BUTTON_PRESSED" and arg == gunSwitchUpBtn then
        switchGun(1)
        return
    end
    
    -- 切换枪械 - 上一把
    if event == "MOUSE_BUTTON_PRESSED" and arg == gunSwitchDnBtn then
        switchGun(-1)
        return
    end
    
    -- 鼠标复位开关
    if event == "MOUSE_BUTTON_PRESSED" and arg == resetPointBtn then
        resetPointState = not resetPointState
        log("Mouse reset: %s", resetPointState and "ON" or "OFF")
        return
    end
    
    -- 配置复位
    if event == "MOUSE_BUTTON_PRESSED" and arg == resetConfigBtn then
        resetConfig()
        return
    end
    
    -- 开始压枪 (压枪开关开启时)
    if event == "MOUSE_BUTTON_PRESSED" and arg == clickBtn and recoilEnabled then
        beginRecoilControl()
    end
end

-- 执行压枪
function beginRecoilControl()
    local gun = getCurrentGun()
    local sleepTime = getSleepTime()
    local firstStepDelay = math.max(1, math.floor((sleepTime * 0.55) + 0.5))
    
    currentBullet = 0
    totalMoveY = 0
    totalMoveX = 0
    errorY = 0  -- 重置误差累加
    errorX = 0
    
    log("Start recoil control: %s, interval=%dms", gun.name, sleepTime)
    log("Pattern steps=%d, inferred shots=%d", #gun.pattern, #gun.pattern + 1)

    if #gun.pattern == 0 then
        return
    end
    
    -- N个弹孔只会得到N-1段补偿，所以首段补偿在第1发开火后再介入。
    if not sleepWhileHolding(firstStepDelay) then
        return
    end
    
    while IsMouseButtonPressed(clickBtn) and currentBullet < #gun.pattern do
        currentBullet = currentBullet + 1
        
        -- 获取当前补偿段的补偿值（小数）
        local rawY, rawX = getBulletRecoil(currentBullet)
        
        -- 应用误差累加，转换为整数移动量
        local moveY, moveX = applyMovement(rawY, rawX)
        
        -- 记录移动量(用于复位)
        totalMoveY = totalMoveY + moveY
        totalMoveX = totalMoveX + moveX
        
        -- 执行鼠标移动补偿
        if moveY ~= 0 or moveX ~= 0 then
            MoveMouseRelative(moveX, moveY)
        end
        
        log("Step #%d -> shot #%d: raw=(%.2f,%.2f) move=(%d,%d) err=(%.2f,%.2f)", 
            currentBullet, currentBullet + 1, rawY, rawX, moveY, moveX, errorY, errorX)
        
        if currentBullet >= #gun.pattern then
            break
        end

        -- 等待下一发
        if not sleepWhileHolding(sleepTime) then
            break
        end
    end
    
    log("Stop at step #%d, totalY=%d, totalX=%d", currentBullet, totalMoveY, totalMoveX)
    
    -- 鼠标复位
    if resetPointState and (totalMoveY ~= 0 or totalMoveX ~= 0) then
        resetMousePosition()
    end
end

-- 复位鼠标位置
function resetMousePosition()
    log("Resetting mouse position...")
    
    -- 快速复位
    local steps = 10
    local stepY = math.floor(-totalMoveY / steps)
    local stepX = math.floor(-totalMoveX / steps)
    
    for i = 1, steps do
        MoveMouseRelative(stepX, stepY)
        Sleep(1)
    end
    
    -- 补偿余数
    local remainY = -totalMoveY - (stepY * steps)
    local remainX = -totalMoveX - (stepX * steps)
    if remainY ~= 0 or remainX ~= 0 then
        MoveMouseRelative(remainX, remainY)
    end
end

-- 复位配置
function resetConfig()
    log("Config reset")
    currentGunIndex = 1
    recoilEnabled = false
    resetPointState = false
    log("Current gun: %s", getCurrentGun().name)
end

structure_info = {
    "Dyck Path" :f"Dyck Path（山峰型）：從（0,0）到（2n,0），分成上升步（U）及下降步（D），其中共計n個上升步與n個下降步且不能畫到x軸以下。",
    "Binary Tree" : f"二元樹（Full Binary Tree）：共計2n條邊、n個實節點、n+1個葉節點，並且透過深度搜尋的方式替每條標邊上號。將所有葉子移除後即為標準二元樹(Standard Binary Tree)。",
    "Non-crossing Arc Diagram" : f"弧線圖（Non-crossing Arc Diagram）：一線上有2n個點，將其分成n個半圓且互相不相交。",
    "Non-crossing Partition" : f"不交叉分割(Non-crossing Partition)：將n邊形的點分組（一組的點數量可為1~n之間的任意正整數），點連上的區域不能與其他點的區域重疊。",
    "Non-intersecting Chord" : f"圓周不相交弦（Non-intersecting Chord）：從圓周上之點1開始按照順序畫點，空心的點為弦的起點，實心的點為弦的終點。任一弦都不可與其他弦相交，圓總共有2n個點及n個弦。",
    "Polygon Triangulation" : f"凸多邊形三角剖分（Polygon Triangulation）：將一個n+2邊形分成n個三角形，先選擇一個固定邊（默認為圖形最上面的邊），再透過優先往三角形之左邊前進的方式來判斷（此時設定此邊為新三角形之固定邊），若左邊沒有三角形，則往該三角形之右邊前進（此時設定此邊為新三角形之固定邊）；若左右都已沒有三角形，則會回到更上一層的三角形右邊繼續前進，直至n個三角形都已經過。",
    "Stack Permutation" : f"堆疊排列（Stack Permutation）：將n個球放入（push）及拿出（pop），球號代表放入次序。",
}

bijec_info = {
    frozenset({"Dyck Path","Binary Tree"}):
            f"",
    frozenset({"Dyck Path","Non-crossing Arc Diagram"}):
            f"",
    frozenset({"Dyck Path","Non-crossing Partition"}):
            f"",
    frozenset({"Dyck Path","Non-intersecting Chord"}):
            f"", 
    frozenset({"Dyck Path","Polygon Triangulation"}):
            f"",  
    frozenset({"Dyck Path","Stack Permutation"}):
            f"",     
}
structure_info = {
    "Dyck Path" :f"Dyck Path(山峰型):從(0,0)到(2n,0),分成上升步(U)及下降步(D),其中共計n個上升步與n個下降步且不能畫到x軸以下。",
    "Binary Tree" : f"二元樹(Full Binary Tree):共計2n條邊、n個實節點、n+1個葉節點,並且透過深度搜尋的方式替每條標邊上號。將所有葉子移除後即為標準二元樹(Standard Binary Tree)。",
    "Non-crossing Arc Diagram" : f"弧線圖(Non-crossing Arc Diagram):一線上有2n個點,將其分成n個半圓且互相不相交。",
    "Non-crossing Partition" : f"不交叉分割(Non-crossing Partition):將n邊形的點分組(一組的點數量可為1~n之間的任意正整數),點連上的區域不能與其他點的區域重疊。",
    "Non-intersecting Chord" : f"圓周不相交弦(Non-intersecting Chord):從圓周上之點1開始按照順序畫點,空心的點為弦的起點,實心的點為弦的終點。任一弦都不可與其他弦相交,圓總共有2n個點及n個弦。",
    "Polygon Triangulation" : f"凸多邊形三角剖分(Polygon Triangulation):將一個n+2邊形分成n個三角形,先選擇一個固定邊(默認為圖形最上面的邊),再透過優先往三角形之左邊前進的方式來判斷(此時設定此邊為新三角形之固定邊),若左邊沒有三角形,則往該三角形之右邊前進(此時設定此邊為新三角形之固定邊);若左右都已沒有三角形,則會回到更上一層的三角形右邊繼續前進,直至n個三角形都已經過。",
    "Stack Permutation" : f"堆疊排列(Stack Permutation):將n個球放入(push)及拿出(pop),球號代表放入次序。",
}

bijec_info = {
    frozenset({"Dyck Path","Binary Tree"}):
            f"當Dyck Path上升一步時,二元樹往左生長;反之Dyck Path下降一步時,二元樹則從同一節點向右生長。並且在兩結構中,Dyck Path 的上升步與與二元樹往左生長之邊用藍色來表示,Dyck Path 的下降步與二元樹往右生長之邊則用紅色表之；且在二元樹中，若邊為虛線，該邊為葉子。",
    frozenset({"Dyck Path","Non-crossing Arc Diagram"}):
            f"當Dyck Path畫一個上升步時,在弧線圖中畫上一點作為弧線起點;反之,當Dyck Path畫一個下降步時,在弧線圖中從起點做一弧至終點。並且透過顏色來表示Dyck Path圖中為一組之上升與下降步,並透過標號表示兩圖在第n步驟之走向。",
    frozenset({"Dyck Path","Non-crossing Partition"}):
            f"在Dyck Path中,第n個上升步可視為不交叉分割圖中的第n頂點,若不同上升步所對應之下降步為一連串下降步,則其對應之不交叉分割之頂點或被分割志同一部分;並且透過虛線與標號來表示Dyck Path圖中為一組之上升與下降步。",
    frozenset({"Dyck Path","Non-intersecting Chord"}):
            f"當Dyck Path畫一個上升步時,在圓中不相交弦畫上一弦之起點;反之,當Dyck Path畫一個下降步時,在圓中不相交弦畫上一弦之終點。並且透過虛線與顏色來表示Dyck Path圖中為一組之上升與下降步,並以相同顏色表示對應到之弦。", 
    frozenset({"Dyck Path","Polygon Triangulation"}):
            f"在凸多邊形三角剖分中，若往某三角形之左邊前進,Dyck Path便獲得一上升步;反之,若往右邊之三角形前進,Dyck Path則獲得一下降步。透過顏色與標號之方式來表達對應,圖多邊形三角剖分中,若是首次進入某三角形,其會照順序為三角形標上號碼且被對應之顏色填滿,Dyck Path隨之獲得一相對應顏色之上升步;若要回至上層,三角形的顏色隨即變成空心(僅剩邊有顏色),且數字標記球也變成空心。",  
    frozenset({"Dyck Path","Stack Permutation"}):
            f"在堆疊排列圖中放入一球可視為在Dyck Path圖獲得一上升步(在兩圖中皆用實心球表示),同理拿出一球代表Dyck Path圖獲得ㄧ下降步(在兩圖中皆用空心球表示);並且在Dyck Path圖中透過顏色以及標號之空心與實心球來表示對應關係。",
    frozenset({"Binary Tree","Non-crossing Arc Diagram"}):
            f"",
    frozenset({"Binary Tree","Non-crossing Partition"}):
            f"",   
    frozenset({"Binary Tree","Non-intersecting Chord"}):
            f"",
    frozenset({"Binary Tree","Polygon Triangulation"}):
            f"",   
    frozenset({"Binary Tree","Stack Permutation"}):
            f"",
}
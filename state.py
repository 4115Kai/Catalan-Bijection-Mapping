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
            f"在凸多邊形三角剖分中,若往某三角形之左邊前進,Dyck Path便獲得一上升步;反之,若往右邊之三角形前進,Dyck Path則獲得一下降步。透過顏色與標號之方式來表達對應,圖多邊形三角剖分中,若是首次進入某三角形,其會照順序為三角形標上號碼且被對應之顏色填滿,Dyck Path隨之獲得一相對應顏色之上升步;若要回至上層,三角形的顏色隨即變成空心(僅剩邊有顏色),且數字標記球也變成空心。",  
    frozenset({"Dyck Path","Stack Permutation"}):
            f"在堆疊排列圖中放入一球可視為在Dyck Path圖獲得一上升步(在兩圖中皆用實心球表示),同理拿出一球代表Dyck Path圖獲得ㄧ下降步(在兩圖中皆用空心球表示);並且在Dyck Path圖中透過顏色以及標號之空心與實心球來表示對應關係。",
    frozenset({"Binary Tree","Non-crossing Arc Diagram"}):
            f"當二元樹往左生長時,是為弧線圖之起點;反之,二元樹往右生長則視為弧線圖之終點。並且二元樹上每邊之號碼可視作弧線圖的步驟數,且在二元樹的同一節點為弧線圖中同一弧線,亦即該點之往左生長邊與往右生長邊上之數為弧線在該步驟開始與結束。",
    frozenset({"Binary Tree","Non-crossing Partition"}):
            f"在二元樹中,第n個往左生長之邊可對應至不交叉分割中的第n頂點,並且透過深度搜尋的方式生成二元樹的邊,若不同節點中往右生長之邊為連續步驟,則對應之頂點會被分割至同一部分,同顏色之邊極為同一節點之往左與往右生長之邊。",   
    frozenset({"Binary Tree","Non-intersecting Chord"}):
            f"當二元樹往左生長時,視為圓周不相交弦之弦起點;反之,二元樹往右生長則視為,視為圓周不相交弦之弦終點。透過深度搜尋的方式替二元樹上每邊之號碼可視作圓周不相交弦的頂點號碼,且在二元樹的同一節點為圓周不相交弦圖中之一弦,亦即該點之往左生長邊與往右生長邊上之數為弧線在該步驟開始與結束。",
    frozenset({"Binary Tree","Polygon Triangulation"}):
            f"透過對偶圖的慨念,先將三角剖分圖中的所有三角形中心點上一點,接著從固定邊出發且以往左為優先,穿過之邊視為新三角形之固定邊;以此類推,直至所有三角形的邊皆已被二元樹的結構通過(除最一開始之固定邊外)。",   
    frozenset({"Binary Tree","Stack Permutation"}):
            f"在二元樹中,若邊是往左生長,及視為在堆疊排列中放入一球；反之,若是往右生長,及視為拿出一球。放入球以實心數字球表示,取出則以空心數字球表示;並將顏色對應至二元樹的邊上,同一節點生長出之兩邊視作同一球的放入與取出(亦可透過深度搜尋之方式為二元樹之邊標號，號碼即為堆疊排列之步驟數)。",
    frozenset({"Non-crossing Arc Diagram","Non-crossing Partition"}):
            f"在弧線圖中,第n個弧線起點可對應至不交叉分割中的第n頂點,並且直線下數字可視作步驟數,若不同弧線終點為連續步驟,則對應之頂點會被分割至同一部分。",
    frozenset({"Non-crossing Arc Diagram","Non-intersecting Chord"}):
            f"將圓周拉成一直線,且點之順序不變,圓上弦的起點(空心點)對應弧線圖中弧線起點;反之,圓上弦的終點(實心點)對應直線上的弧線之終點,且在兩張圖中,顏色相同之弦與弧線極為對應之弦與弧。",
    frozenset({"Non-crossing Arc Diagram","Polygon Triangulation"}):
            f"在凸多邊形的三角剖分中,若沿著對偶圖的結構向左側的子三角形前進,則在弧線圖中的對應序列中標上該弧線的起點;反之,若向右側之三角形前進,則標上該弧線的終點。若用顏色做對應,在凸多邊形三角剖分中一組顏色只會有兩條線(左線跟右線),對應到弧線圖的起點跟終點。",
    frozenset({"Non-crossing Arc Diagram","Stack Permutation"}):
            f"弧線圖半圓的起點(空心點)對應堆疊排列的放入(push),半圓的終點(實心點)對應堆疊排列的拿出(pop),若用顏色對應,在堆疊排列中,相同顏色之球與弧線及為彼此對應。",
    frozenset({"Non-crossing Partition","Non-intersecting Chord"}):
            f"在圓中不相交弦中,第n條弦之起點可對應至不交叉分割中的第n頂點,並且圓周點上數字可視作步驟數,若不同弦之終點為連續數字,則對應之頂點會被分割至同一部分。",
    frozenset({"Non-crossing Partition","Polygon Triangulation"}):
            f"在三角剖分圖以向三角形左邊前進為主,若b三角形在a三角形之左邊,則不交叉分割圖中a、b頂點會被分在同一組;以此類推,直至n個三角形都確認完成。",
    frozenset({"Non-crossing Partition","Stack Permutation"}):
            f"在堆疊排列圖中,將第n球之放入(push)可視作不交叉分割中第n頂點,若在堆疊排列圖中球是被連續取出(及過程中無放入任何球),球之號碼所對應到的頂點即被分割在同一部分。",
    frozenset({"Non-intersecting Chord","Polygon Triangulation"}):
            f"在凸多邊形的三角剖分中，,若沿著對偶圖的結構向左側之三角形前進,則在圓中不相交弦中標上該弦的起點;反之,若向右側之三角形前進,則標上該弦的終點,且在兩圖中，顏色相同之弦與三角形即為彼此對應。",
    frozenset({"Non-intersecting Chord","Stack Permutation"}):
            f"在圓中不相交弦中,弦的起點(實心點)對應到堆疊排列的放入(push)；反之，弦的終點(空心點)對應到堆疊排列的放入(push) ,且在兩圖中，顏色相同之弦與球即為彼此對應。",
    frozenset({"Polygon Triangulation","Stack Permutation"}):
            f"在圖多邊形三角剖分圖中,以向左前進為主,直至左邊已無三角形,此時會回到上一個三角形,以此類推至全部三角形之左右皆已確認過。且向左前進時可視為在堆疊排量中放入一球,第n個經過之三角形及視為第n球;回到上一個三角形則視為取出一球。",
}
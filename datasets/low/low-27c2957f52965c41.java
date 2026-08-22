package org.apache.ibatis.scripting.xmltags;
import java.util.Iterator;
import java.util.List;

public class ChooseSqlNode implements SqlNode {
   private SqlNode defaultSqlNode;
   private List<SqlNode> ifSqlNodes;

   public ChooseSqlNode(List<SqlNode> ifSqlNodes, SqlNode defaultSqlNode) {
      this.ifSqlNodes = ifSqlNodes;
      this.defaultSqlNode = defaultSqlNode;
   }

   public boolean apply(DynamicContext context) {
      Iterator var2 = this.ifSqlNodes.iterator();

      SqlNode sqlNode;
      do {
         if (!var2.hasNext()) {
            if (this.defaultSqlNode != null) {
               this.defaultSqlNode.apply(context);
               return true;
            }

            return false;
         }

         sqlNode = (SqlNode)var2.next();
      } while(!sqlNode.apply(context));

      return true;
   }
}

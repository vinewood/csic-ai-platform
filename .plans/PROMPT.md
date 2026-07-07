# Ralph Loop Prompt — 中船党校前端验证

@.plans/PRD.md @.plans/progress.txt

## 任务
迭代完成前端开发任务清单，直到所有任务状态为 PASS。

## 迭代步骤
1. 从 PRD.md 中找到最高优先级的未完成任务
2. 检查相关代码和模板文件，理解当前状态
3. 修改代码完成任务要求
4. 启动服务并验证：`curl -s -k http://localhost:8000/[页面路径] | grep -c "<html"`
5. 如果验证通过，在 PRD.md 中将对应状态标记为 PASS
6. 将本次迭代的经验追加到 progress.txt
7. 如果有错误，修复后重新验证

## 完成条件
当所有任务状态为 PASS 时，输出：
<promise>COMPLETE</promise>

注意：每次只做一个任务。质量优先。

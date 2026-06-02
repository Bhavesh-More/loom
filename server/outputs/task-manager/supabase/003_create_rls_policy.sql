CREATE POLICY tasks_select_policy ON tasks FOR SELECT USING (true);
CREATE POLICY tasks_insert_policy ON tasks FOR INSERT WITH CHECK (true);
CREATE POLICY tasks_update_policy ON tasks FOR UPDATE USING (true) WITH CHECK (true);
CREATE POLICY tasks_delete_policy ON tasks FOR DELETE USING (true);
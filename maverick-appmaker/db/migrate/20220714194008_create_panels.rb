class CreatePanels < ActiveRecord::Migration[7.0]
  def change
    create_table :panels do |t|
      t.string :title
      t.string :panel_type
      t.text :natural_prompt
      t.text :sql_query
      t.references :flow, null: false, foreign_key: true

      t.timestamps
    end
  end
end

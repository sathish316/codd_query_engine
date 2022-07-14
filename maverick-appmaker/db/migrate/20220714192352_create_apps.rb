class CreateApps < ActiveRecord::Migration[7.0]
  def change
    create_table :apps do |t|
      t.string :name
      t.text :schema
      t.string :databasetype
      t.string :engine_config

      t.timestamps
    end
  end
end

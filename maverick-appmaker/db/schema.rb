# This file is auto-generated from the current state of the database. Instead
# of editing this file, please use the migrations feature of Active Record to
# incrementally modify your database, and then regenerate this schema definition.
#
# This file is the source Rails uses to define your schema when running `bin/rails
# db:schema:load`. When creating a new database, `bin/rails db:schema:load` tends to
# be faster and is potentially less error prone than running all of your
# migrations from scratch. Old migrations may fail to apply correctly if those
# migrations use external dependencies or application code.
#
# It's strongly recommended that you check this file into your version control system.

ActiveRecord::Schema[7.0].define(version: 2022_07_14_194008) do
  create_table "apps", force: :cascade do |t|
    t.string "name"
    t.text "schema"
    t.string "databasetype"
    t.string "engine_config"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
  end

  create_table "flows", force: :cascade do |t|
    t.string "name"
    t.integer "app_id", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["app_id"], name: "index_flows_on_app_id"
  end

  create_table "panels", force: :cascade do |t|
    t.string "title"
    t.string "panel_type"
    t.text "natural_prompt"
    t.text "sql_query"
    t.integer "flow_id", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["flow_id"], name: "index_panels_on_flow_id"
  end

  add_foreign_key "flows", "apps"
  add_foreign_key "panels", "flows"
end

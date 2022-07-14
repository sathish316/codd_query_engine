require "application_system_test_case"

class FlowsTest < ApplicationSystemTestCase
  setup do
    @flow = flows(:one)
  end

  test "visiting the index" do
    visit flows_url
    assert_selector "h1", text: "Flows"
  end

  test "should create flow" do
    visit flows_url
    click_on "New flow"

    fill_in "App", with: @flow.app_id
    fill_in "Name", with: @flow.name
    click_on "Create Flow"

    assert_text "Flow was successfully created"
    click_on "Back"
  end

  test "should update Flow" do
    visit flow_url(@flow)
    click_on "Edit this flow", match: :first

    fill_in "App", with: @flow.app_id
    fill_in "Name", with: @flow.name
    click_on "Update Flow"

    assert_text "Flow was successfully updated"
    click_on "Back"
  end

  test "should destroy Flow" do
    visit flow_url(@flow)
    click_on "Destroy this flow", match: :first

    assert_text "Flow was successfully destroyed"
  end
end

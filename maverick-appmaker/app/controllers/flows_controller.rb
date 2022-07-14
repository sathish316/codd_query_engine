class FlowsController < ApplicationController
  before_action :set_flow, only: %i[ show edit update destroy ]

  # GET /flows or /flows.json
  def index
    if params[:app_id]
      @app = App.find(params[:app_id])
      @flows = Flow.where(app_id: params[:app_id])
    else
      @flows = Flow.all
    end
  end

  # GET /flows/1 or /flows/1.json
  def show
    if params[:app_id]
      @app = App.find(params[:app_id])
    end
    @flow = Flow.find(params[:id])
  end

  # GET /flows/new
  def new
    @flow = Flow.new
  end

  # GET /flows/1/edit
  def edit
  end

  # POST /flows or /flows.json
  def create
    @flow = Flow.new(flow_params)

    respond_to do |format|
      if @flow.save
        format.html { redirect_to flow_url(@flow), notice: "Flow was successfully created." }
        format.json { render :show, status: :created, location: @flow }
      else
        format.html { render :new, status: :unprocessable_entity }
        format.json { render json: @flow.errors, status: :unprocessable_entity }
      end
    end
  end

  # PATCH/PUT /flows/1 or /flows/1.json
  def update
    respond_to do |format|
      if @flow.update(flow_params)
        format.html { redirect_to flow_url(@flow), notice: "Flow was successfully updated." }
        format.json { render :show, status: :ok, location: @flow }
      else
        format.html { render :edit, status: :unprocessable_entity }
        format.json { render json: @flow.errors, status: :unprocessable_entity }
      end
    end
  end

  # DELETE /flows/1 or /flows/1.json
  def destroy
    @flow.destroy

    respond_to do |format|
      format.html { redirect_to flows_url, notice: "Flow was successfully destroyed." }
      format.json { head :no_content }
    end
  end

  private
    # Use callbacks to share common setup or constraints between actions.
    def set_flow
      @flow = Flow.find(params[:id])
    end

    # Only allow a list of trusted parameters through.
    def flow_params
      params.require(:flow).permit(:name, :app_id)
    end
end

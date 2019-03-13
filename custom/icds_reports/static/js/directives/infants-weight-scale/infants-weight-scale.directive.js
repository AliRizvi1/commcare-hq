/* global d3 */
var url = hqImport('hqwebapp/js/initial_page_data').reverse;

function InfantsWeightScaleController($scope, $routeParams, $location, $filter, infrastructureService,
    locationsService, userLocationId, storageService, haveAccessToAllLocations, baseControllersService) {
    baseControllersService.BaseController.call(this, $scope, $routeParams, $location, locationsService,
        userLocationId, storageService, haveAccessToAllLocations);
    var vm = this;
    vm.label = "AWCs Reported Weighing Scale: Infants";
    vm.steps = {
        'map': {route: '/awc_infrastructure/infants_weight_scale/map', label: 'Map View'},
        'chart': {route: '/awc_infrastructure/infants_weight_scale/chart', label: 'Chart View'},
    };
    vm.data = {
        legendTitle: 'Percentage',
    };
    vm.filters = ['gender', 'age', 'ageServiceDeliveryDashboard'];
    vm.rightLegend = {
        info: 'Of the AWCs that have submitted an Infrastructure Details form, the percentage of AWCs that reported having a weighing scale for infants',
    };

    vm.templatePopup = function(loc, row) {
        var inMonth = row ? $filter('indiaNumbers')(row.in_month) : 'N/A';
        var percent = row ? d3.format('.2%')(row.in_month / (row.all || 1)) : "N/A";
        return vm.createTemplatePopup(
            loc.properties.name,
            [{
                indicator_name: 'Total of AWCs that reported having a weighing scale for infants: ',
                indicator_value: inMonth,
            },
            {
                indicator_name: 'Percentage of AWCs that reported having a weighing scale for infants: ',
                indicator_value: percent,
            }]
        );
    };

    vm.loadData = function () {
        vm.setStepsMapLabel();
        var usePercentage = true;
        var forceYAxisFromZero = false;
        vm.myPromise = infrastructureService.getInfantsWeightScaleData(vm.step, vm.filtersData).then(
            vm.loadDataFromResponse(usePercentage, forceYAxisFromZero)
        );
    };

    vm.init();

    var options = {
        'xAxisTickFormat': '%b %Y',
        'yAxisTickFormat': ".2%",
        'captionContent': ' Of the AWCs that have submitted an Infrastructure Details form, the percentage of AWCs that reported having a weighing scale for infants',
    };
    vm.chartOptions = vm.getChartOptions(options);
    vm.chartOptions.chart.color = d3.scale.category10().range();

    vm.tooltipContent = function (monthName, dataInMonth) {
        return vm.createTooltipContent(
            monthName,
            [{
                indicator_name: 'Number of AWCs that reported having a weighing scale for infants: ',
                indicator_value: $filter('indiaNumbers')(dataInMonth.in_month),
            },
            {
                indicator_name: 'Percentage of AWCs that reported having a weighing scale for infants: ',
                indicator_value: d3.format('.2%')(dataInMonth.y),
            }]
        );
    };
}

InfantsWeightScaleController.$inject = ['$scope', '$routeParams', '$location', '$filter', 'infrastructureService', 'locationsService', 'userLocationId', 'storageService', 'haveAccessToAllLocations', 'baseControllersService'];

window.angular.module('icdsApp').directive('infantsWeightScale', function() {
    return {
        restrict: 'E',
        templateUrl: url('icds-ng-template', 'map-chart'),
        bindToController: true,
        scope: {
            data: '=',
        },
        controller: InfantsWeightScaleController,
        controllerAs: '$ctrl',
    };
});
